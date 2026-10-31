import{f as B}from"./freeze-2CouKnFP.js";(function(){var n=document.getElementById("aurora-gl");if(!n)return;var e=n.getContext("webgl2",{antialias:!1,alpha:!1,depth:!1,powerPreference:"low-power"});if(!e){n.style.display="none";return}var I=`#version 300 es
void main(){ vec2 p=vec2((gl_VertexID<<1)&2, gl_VertexID&2); gl_Position=vec4(p*2.0-1.0,0.0,1.0); }`,z=`#version 300 es
precision highp float;
precision highp int;
out vec4 o;
uniform vec2 u_res; uniform float u_time; uniform vec2 u_mouse; uniform float u_light;
uniform float u_dither;
float hash(vec2 p){ return fract(sin(dot(p,vec2(41.3,289.1)))*43758.5453); }
/* One code value of noise per pixel, from an integer hash rather than the
   sine one above: at gl_FragCoord magnitudes the sine hash loses its low
   bits to the argument reduction and starts to repeat. */
float dither(){ uint h=uint(gl_FragCoord.x)+uint(gl_FragCoord.y)*1973u;
  h=(h^(h>>15))*2246822519u; h=(h^(h>>13))*3266489917u;
  return float((h^(h>>16))&0xffffu)/65535.0-0.5; }
float noise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.0-2.0*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),u.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x),u.y); }
/* Three octaves, where the reference used five. The two dropped octaves
   hold 2.5% of the noise variance but 40% of its samples: every octave is
   four hash (sine) calls, and fbm runs three times per band across three
   bands, so this one line is most of what the veil costs per pixel. The
   noise is 0..1 rather than zero-mean, so dropping octaves also moves its
   mean; +0.06447 is the mean of the two weights that left
   (0.5*(0.0831875+0.0457531)), which puts every use of this value back
   where it was and removes only the finest grain. */
float fbm(vec2 p){ float v=0.0,a=0.5; for(int i=0;i<3;i++){ v+=a*noise(p); p=p*1.9+3.0; a*=0.55; } return v+0.06447; }
vec3 auroraPal(float t){
  return mix(mix(vec3(0.10,0.9,0.45), vec3(0.15,0.8,0.85), smoothstep(0.0,0.5,t)),
             vec3(0.6,0.35,0.95), smoothstep(0.5,1.0,t));
}
void main(){
  vec2 uv=gl_FragCoord.xy/u_res;
  vec2 p=(gl_FragCoord.xy-0.5*u_res)/u_res.y;
  float sway=(u_mouse.x-0.5)*1.2;
  /* night sky, or a pale sky in light mode */
  vec3 night=mix(vec3(0.02,0.03,0.09), vec3(0.03,0.06,0.16), uv.y);
  vec3 day  =mix(vec3(0.97,0.98,1.00), vec3(0.90,0.94,0.99), uv.y);
  vec3 col=mix(night, day, u_light);
  /* No stars. Three rounds of layering and jittering still read as a
     pattern at full-screen scale, and a starfield that looks generated is
     worse than none. The sky keeps its gradient; the only light in it is
     the curtains. */
  float t=u_time*0.15;
  for(int i=0;i<3;i++){
    float fi=float(i);
    float base=(fi-1.0)*0.55 + sway*(0.35+fi*0.2);
    float cx=base + sin(p.y*1.6 + t*2.0 + fi*2.1)*0.22 + (fbm(vec2(p.y*1.2+fi*3.0, t*1.5))-0.5)*0.7;
    float w=0.15 + 0.09*fbm(vec2(p.y*3.0+fi, t));
    float band=exp(-pow((p.x-cx)/w, 2.0));
    float vert=smoothstep(-0.95,0.8,p.y) * (0.45+0.55*fbm(vec2(p.x*5.0+fi*4.0, p.y*2.6 - t*2.5)));
    float ribbon=band*vert;
    /* Hue is a function of position and band only — never of time. The
       reference adds \`t*0.3\` here, which walks the whole palette through
       every band on a slow cycle; because it drifts uniformly with height,
       the phase boundary reads as a horizontal colour seam sweeping up the
       screen. Freezing it keeps each curtain its own colour, and the motion
       still comes from the snaking centre and the noise. */
    float hue=fract(0.12 + fi*0.28 + p.y*0.16);
    vec3 tint=auroraPal(hue);
    /* light mode: the saturated curtain would shout on white, so it keeps
       its shape and loses most of its chroma, blended toward the page */
    tint=mix(tint, mix(tint, vec3(0.62,0.70,0.86), 0.55), u_light);
    col += tint * ribbon * (1.0 - fi*0.14) * mix(1.0, 0.55, u_light);
  }
  col *= 0.7+0.5*smoothstep(1.5,0.1,length(p*vec2(0.6,1.0)));
  col=col/(col+0.8);
  /* Dither, in output space and after the tone curve, where 1/255 is exactly
     one code value of the framebuffer. The sky ramps slower than that: it
     spends tens of rows inside one value and then steps down by one, and on
     an OLED at night those steps read as thin horizontal lines. u_dither is
     a width in code values; the caller pre-emphasises it by the upscale
     factor, because the browser averages it again on the way to the screen. */
  vec3 c=pow(max(col,0.0),vec3(0.9))+dither()*(u_dither/255.0);
  o=vec4(c,1.0);
}`;function E(t,r){var a=e.createShader(t);if(e.shaderSource(a,r),e.compileShader(a),!e.getShaderParameter(a,e.COMPILE_STATUS))throw new Error(e.getShaderInfoLog(a)||"shader compile failed");return a}var i=null,T=null,S=null,M=null,P=null,A=null;function k(){try{if(i=e.createProgram(),e.attachShader(i,E(e.VERTEX_SHADER,I)),e.attachShader(i,E(e.FRAGMENT_SHADER,z)),e.linkProgram(i),!e.getProgramParameter(i,e.LINK_STATUS))throw new Error(e.getProgramInfoLog(i)||"link failed")}catch{return n.style.display="none",i=null,!1}return e.useProgram(i),T=e.getUniformLocation(i,"u_res"),S=e.getUniformLocation(i,"u_time"),M=e.getUniformLocation(i,"u_mouse"),P=e.getUniformLocation(i,"u_light"),A=e.getUniformLocation(i,"u_dither"),!0}if(!k())return;var s=window.matchMedia("(prefers-reduced-motion: reduce)"),x=B(),o=[.5,.5],v=[.5,.5],h=0,c=0,b=0,p=0,g=0,C=320,H=11.5;function F(){g=document.documentElement.getAttribute("data-theme")==="light"?1:0}var O=.7,w=!0,N=1;function V(){var t=window.innerWidth>1200?1.5:2;return Math.min(window.devicePixelRatio||1,t)*O}function W(){var t=(window.devicePixelRatio||1)/Math.max(N,.001);return Math.max(1,Math.min(2,t))}function y(){w=!1;var t=V(),r=Math.round(window.innerWidth*t),a=Math.round(window.innerHeight*t);N=r/Math.max(window.innerWidth,1)||1,!(r===n.width&&a===n.height)&&(n.width=r,n.height=a,e.viewport(0,0,r,a))}var u=[0,0],_=-1,f=[NaN,NaN],L=-1;function q(){u[0]=0,u[1]=0,_=-1,f[0]=NaN,f[1]=NaN,L=-1}function R(t){(n.width!==u[0]||n.height!==u[1])&&(e.uniform2f(T,n.width,n.height),u[0]=n.width,u[1]=n.height),g!==_&&(e.uniform1f(P,g),_=g);var r=W();r!==L&&(e.uniform1f(A,r),L=r),(o[0]!==f[0]||o[1]!==f[1])&&(e.uniform2f(M,o[0],o[1]),f[0]=o[0],f[1]=o[1]),e.uniform1f(S,t),e.drawArrays(e.TRIANGLES,0,3)}function U(t){w&&y();var r=p?Math.min(64,t-p):16.7;p=t;var a=1-Math.exp(-r/C);o[0]+=(v[0]-o[0])*a,o[1]+=(v[1]-o[1])*a,R((b+(t-c))/1e3),h=requestAnimationFrame(U)}function l(){y(),R(H)}function d(){if(s.matches){l();return}if(x){l();return}h||(c=performance.now()-b,p=0,h=requestAnimationFrame(U))}function m(){h&&cancelAnimationFrame(h),h=0,c&&(b=performance.now()-c,c=0)}window.addEventListener("pointermove",function(t){v[0]=t.clientX/window.innerWidth,v[1]=1-t.clientY/window.innerHeight},{passive:!0}),window.addEventListener("resize",function(){w=!0,s.matches||x?l():h||y()}),n.addEventListener("webglcontextlost",function(t){t.preventDefault(),m(),i=null}),n.addEventListener("webglcontextrestored",function(){k()&&(q(),e.viewport(0,0,n.width,n.height),w=!0,d())});function D(){s.matches?(m(),l()):d()}s.addEventListener?s.addEventListener("change",D):s.addListener&&s.addListener(D),document.addEventListener("visibilitychange",function(){document.hidden?m():d()}),F(),d(),window.KBPAurora={repaint:function(){F(),s.matches||!h?l():y()},stop:m,resume:d,freeze:function(){x=!0,m(),l()}}})();
