import os, re, json, uuid, shutil, subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
ROOT=Path(__file__).parent.resolve(); OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
app=Flask(__name__,template_folder='templates',static_folder='static')

def font(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/freefont/FreeSans.ttf','C:/Windows/Fonts/arial.ttf']:
        if Path(p).exists():
            try:return ImageFont.truetype(p,size)
            except:pass
    return ImageFont.load_default()
def wrap(draw,txt,f,maxw):
    out=[]; line=''
    for word in txt.split():
        test=(line+' '+word).strip()
        if draw.textbbox((0,0),test,font=f)[2]<=maxw:line=test
        else:
            if line:out.append(line)
            line=word
    if line:out.append(line)
    return out
def make_card(path,title,body,i,n,vertical):
    w,h=(720,1280) if vertical else (1280,720); colors=[(34,79,99),(75,52,112),(28,94,75),(104,55,62),(36,70,130)]; c=colors[(i-1)%len(colors)]
    im=Image.new('RGB',(w,h),c); d=ImageDraw.Draw(im)
    for j in range(9):
        x=(j*173+i*41)%w;y=(j*113+i*59)%h;r=30+(j*13)%90
        d.ellipse((x-r,y-r,x+r,y+r),fill=(min(c[0]+15,255),min(c[1]+20,255),min(c[2]+24,255)))
    d.rounded_rectangle((int(w*.07),int(h*.20),int(w*.93),int(h*.80)),radius=28,fill=(8,12,28))
    small=font(22); tf=font(42 if vertical else 48); bf=font(34 if vertical else 32)
    d.text((int(w*.10),int(h*.25)),f'SCENE {i}/{n}',font=small,fill=(255,214,102)); y=int(h*.34)
    for line in wrap(d,title,tf,int(w*.76))[:3]:d.text((int(w*.10),y),line,font=tf,fill='white');y+=58
    y+=22
    for line in wrap(d,body,bf,int(w*.76))[:7]:d.text((int(w*.10),y),line,font=bf,fill=(231,237,255));y+=45
    d.text((int(w*.10),int(h*.84)),'AI VIDEO MAKER • Hindi',font=small,fill=(210,220,240));im.save(path,quality=92)
def fallback(topic,kind):
    if kind=='Horror': title=topic or 'आधी रात का रहस्य'; beats=['रात के बारह बजे, पुराने घर से अजीब आवाज़ आने लगी।','रवि ने दरवाज़ा खोला, लेकिन अंदर कोई दिखाई नहीं दिया।','दीवार पर अचानक एक परछाईं हिलने लगी।','पीछे से धीमी आवाज़ आई—तुम यहाँ क्यों आए?','रवि भागा, तभी सुबह की रोशनी फैल गई।','लेकिन उसके फोन में एक नई तस्वीर थी… जिसमें वह घर के अंदर खड़ा था।']
    elif kind=='Kids': title=topic or 'चतुर खरगोश और मददगार दोस्त'; beats=['एक हरे-भरे जंगल में चिंटू खरगोश रहता था।','एक दिन उसे रास्ते में परेशान चिड़िया मिली।','चिंटू ने पेड़ से गिरी टहनी हटाकर उसका रास्ता साफ किया।','चिड़िया ने अपने दोस्तों को बुलाया और सबने मिलकर मदद की।','शाम तक जंगल फिर से खुशियों से भर गया।','चिंटू ने सीखा—मिलकर मदद करने से हर मुश्किल आसान होती है।']
    else: title=topic or 'जादुई जंगल का रहस्य'; beats=['एक रहस्यमयी जंगल में दो दोस्त रास्ता भटक गए।','उन्हें चमकता हुआ एक छोटा दरवाज़ा दिखाई दिया।','दरवाज़े के पीछे एक नन्हा खरगोश मदद माँग रहा था।','दोनों दोस्तों ने मिलकर उसे बाहर निकाला।','खरगोश ने उन्हें जंगल से बाहर जाने का रास्ता दिखाया।','दोनों ने जाना कि दया और हिम्मत सबसे बड़ा जादू है।']
    return title,[{'title':title,'text':b} for b in beats]
def ai_script(topic,kind,duration):
    key=os.getenv('GEMINI_API_KEY')
    if not key:return None
    try:
        import requests
        prompt=('Return only valid JSON with keys title and scenes. scenes must be 6 objects with title and text. Write an original Hindi YouTube script. Keep kids content gentle; horror atmospheric, no graphic gore. '
                f'Video type: {kind}. Topic: {topic or "invent a catchy topic"}. Target length: {duration}.')
        url='https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
        r=requests.post(url,params={'key':key},json={'contents':[{'parts':[{'text':prompt}]}]},timeout=35);r.raise_for_status()
        raw=r.json()['candidates'][0]['content']['parts'][0]['text'];raw=re.sub(r'^```(?:json)?|```$','',raw.strip(),flags=re.M).strip();data=json.loads(raw)
        if data.get('scenes'):return data.get('title',topic or 'मेरी कहानी'),data['scenes'][:10]
    except Exception as e:app.logger.warning('AI script fallback: %s',e)
    return None
@app.get('/')
def home():return render_template('index.html')
@app.post('/api/generate')
def generate():
    p=request.get_json(force=True);topic=str(p.get('topic','')).strip()[:180];kind=p.get('videoType','Both');duration=p.get('duration','1 minute');vertical=p.get('ratio')=='9:16';voice=bool(p.get('voice',True))
    ai=ai_script(topic,kind,duration)
    if ai:title,scenes=ai
    else:title,scenes=fallback(topic,'Horror' if kind=='Horror' else ('Kids' if kind=='Kids' else 'Both'))
    job=uuid.uuid4().hex[:10];folder=OUT/job;folder.mkdir(parents=True,exist_ok=True);cards=[];narr=[]
    target_secs={'30 seconds':30,'1 minute':60,'3 minutes':180,'5 minutes':300}.get(duration,60)
    for i,s in enumerate(scenes,1):
        path=folder/f'scene_{i:02d}.jpg';txt=str(s.get('text',''))[:700];make_card(path,str(s.get('title',title))[:100],txt,i,len(scenes),vertical);cards.append(path);narr.append(txt)
    audio=folder/'voice.mp3';audio_ok=False
    if voice:
        try:gTTS(text='।'.join(narr),lang='hi').save(str(audio));audio_ok=True
        except Exception as e:app.logger.warning('TTS unavailable: %s',e)
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:return jsonify(error='FFmpeg is not installed on the server. Install FFmpeg and restart.'),500
    concat=folder/'images.txt'
    with concat.open('w',encoding='utf-8') as f:
        for c in cards:f.write(f"file '{c.as_posix()}'\nduration {target_secs/len(cards):.3f}\n")
        f.write(f"file '{cards[-1].as_posix()}'\n")
    video=folder/'video.mp4';cmd=[ffmpeg,'-y','-f','concat','-safe','0','-i',str(concat)]
    if audio_ok:cmd+=['-i',str(audio)]
    else:cmd+=['-f','lavfi','-i','anullsrc=channel_layout=stereo:sample_rate=44100']
    cmd+=['-t',str(target_secs),'-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(video)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
    if result.returncode:return jsonify(error='FFmpeg rendering failed. Check server logs.'),500
    return jsonify(jobId=job,title=title,sceneCount=len(scenes),videoUrl=f'/outputs/{job}/video.mp4',script=scenes,voiceGenerated=audio_ok,mode='AI script' if ai else 'Built-in starter script')
@app.get('/outputs/<job>/<path:filename>')
def output(job,filename):
    folder=(OUT/job).resolve()
    if not str(folder).startswith(str(OUT.resolve())):return 'Invalid path',400
    return send_from_directory(folder,filename,as_attachment=filename.endswith('.mp4'))
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
