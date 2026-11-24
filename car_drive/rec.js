const {chromium}=require('playwright');const {spawn}=require('child_process');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage({viewport:{width:1080,height:1080}});
p.on('console',m=>console.log(m.text()));p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+__dirname+'/scene.html');await p.waitForFunction('window.ready');
const ff=spawn('ffmpeg',['-y','-f','image2pipe','-framerate','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-crf','18','-movflags','+faststart',__dirname+'/car_drive_square.mp4'],{stdio:['pipe','ignore','inherit']});
const N=+process.argv[2]||300;for(let i=0;i<N;i++){await p.evaluate(t=>renderFrame(t),i/30);ff.stdin.write(await p.screenshot({type:'jpeg',quality:92}));}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();})();
