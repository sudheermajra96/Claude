// usage: node rec.js [fps] [preview t1,t2,...]
const {chromium}=require('playwright');const {spawn}=require('child_process');const fs=require('fs');
(async()=>{const fps=+process.argv[2]||30,prev=process.argv[3];
const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+__dirname+'/scene.html');await p.waitForFunction('window.ready');
const ad=await p.evaluate('window.audioData');fs.writeFileSync(__dirname+'/events.json',JSON.stringify(ad));
if(prev){for(const t of prev.split(',')){await p.evaluate(t=>renderFrame(t),+t);await p.screenshot({path:`${__dirname}/prev_${t}.jpg`,type:'jpeg',quality:85});}await b.close();return;}
const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',''+fps,'-i','-','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p',__dirname+'/_video_only.mp4'],{stdio:['pipe','inherit','inherit']});
const N=Math.round(ad.T*fps);for(let i=0;i<N;i++){await p.evaluate(t=>renderFrame(t),i/fps);ff.stdin.write(await p.screenshot({type:'jpeg',quality:93}));}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();})();
