import{A as e,B as t,D as n,I as r,J as i,O as a,Y as o,Z as s,at as c,h as l,j as u,m as d,tt as f,u as p,w as m}from"./request-CurBmZR-.js";import{a as h,l as g,m as _,s as v}from"./use-message-CKeZxwH0.js";import{At as y,Bt as b,D as x,F as S,I as C,It as w,K as T,Lt as E,O as D,Rt as O,U as k,Vt as A,Z as j,gt as ee,jt as M,k as N,nt as te,q as P,rt as F,tt as ne,vt as re,x as ie,y as ae,yt as oe,zt as I}from"./light-DN_jvUNJ.js";import{t as L}from"./Add-pRnqMpnD.js";import{H as se,T as R,V as z,a as ce}from"./index-CSxK0_HK.js";var B=ne(`.v-x-scroll`,{overflow:`auto`,scrollbarWidth:`none`},[ne(`&::-webkit-scrollbar`,{width:0,height:0})]),le=m({name:`XScroll`,props:{disabled:Boolean,onScroll:Function},setup(){let e=f(null);function t(e){!(e.currentTarget.offsetWidth<e.currentTarget.scrollWidth)||e.deltaY===0||(e.currentTarget.scrollLeft+=e.deltaY+e.deltaX,e.preventDefault())}let n=F();return B.mount({id:`vueuc/x-scroll`,head:!0,anchorMetaName:te,ssr:n}),Object.assign({selfRef:e,handleWheel:t},{scrollTo(...t){var n;(n=e.value)==null||n.scrollTo(...t)}})},render(){return n(`div`,{ref:`selfRef`,onScroll:this.onScroll,onWheel:this.disabled?void 0:this.handleWheel,class:`v-x-scroll`},this.$slots)}}),ue=/\s/;function de(e){for(var t=e.length;t--&&ue.test(e.charAt(t)););return t}var V=/^\s+/;function H(e){return e&&e.slice(0,de(e)+1).replace(V,``)}var U=NaN,fe=/^[-+]0x[0-9a-f]+$/i,pe=/^0b[01]+$/i,W=/^0o[0-7]+$/i,G=parseInt;function K(e){if(typeof e==`number`)return e;if(D(e))return U;if(x(e)){var t=typeof e.valueOf==`function`?e.valueOf():e;e=x(t)?t+``:t}if(typeof e!=`string`)return e===0?e:+e;e=H(e);var n=pe.test(e);return n||W.test(e)?G(e.slice(2),n?2:8):fe.test(e)?U:+e}var q=function(){return N.Date.now()},me=`Expected a function`,he=Math.max,ge=Math.min;function J(e,t,n){var r,i,a,o,s,c,l=0,u=!1,d=!1,f=!0;if(typeof e!=`function`)throw TypeError(me);t=K(t)||0,x(n)&&(u=!!n.leading,d=`maxWait`in n,a=d?he(K(n.maxWait)||0,t):a,f=`trailing`in n?!!n.trailing:f);function p(t){var n=r,a=i;return r=i=void 0,l=t,o=e.apply(a,n),o}function m(e){return l=e,s=setTimeout(_,t),u?p(e):o}function h(e){var n=e-c,r=e-l,i=t-n;return d?ge(i,a-r):i}function g(e){var n=e-c,r=e-l;return c===void 0||n>=t||n<0||d&&r>=a}function _(){var e=q();if(g(e))return v(e);s=setTimeout(_,h(e))}function v(e){return s=void 0,f&&r?p(e):(r=i=void 0,o)}function y(){s!==void 0&&clearTimeout(s),l=0,r=c=i=s=void 0}function b(){return s===void 0?o:v(q())}function S(){var e=q(),n=g(e);if(r=arguments,i=this,c=e,n){if(s===void 0)return m(c);if(d)return clearTimeout(s),s=setTimeout(_,t),p(c)}return s===void 0&&(s=setTimeout(_,t)),o}return S.cancel=y,S.flush=b,S}var _e=`Expected a function`;function ve(e,t,n){var r=!0,i=!0;if(typeof e!=`function`)throw TypeError(_e);return x(n)&&(r=`leading`in n?!!n.leading:r,i=`trailing`in n?!!n.trailing:i),J(e,t,{leading:r,maxWait:t,trailing:i})}var Y=v(`n-tabs`),ye={tab:[String,Number,Object,Function],name:{type:[String,Number],required:!0},disabled:Boolean,displayDirective:{type:String,default:`if`},closable:{type:Boolean,default:void 0},tabProps:Object,label:[String,Number,Object,Function]},X=m({__TAB_PANE__:!0,name:`TabPane`,alias:[`TabPanel`],props:ye,slots:Object,setup(e){let t=a(Y,null);return t||h(`tab-pane`,"`n-tab-pane` must be placed inside `n-tabs`."),{style:t.paneStyleRef,class:t.paneClassRef,mergedClsPrefix:t.mergedClsPrefixRef}},render(){return n(`div`,{class:[`${this.mergedClsPrefix}-tab-pane`,this.class],style:this.style},this.$slots)}}),Z=m({__TAB__:!0,inheritAttrs:!1,name:`Tab`,props:Object.assign({internalLeftPadded:Boolean,internalAddable:Boolean,internalCreatedByPane:Boolean},se(ye,[`displayDirective`])),setup(e){let{mergedClsPrefixRef:t,valueRef:n,typeRef:r,closableRef:i,tabStyleRef:o,addTabStyleRef:s,tabClassRef:c,addTabClassRef:u,tabChangeIdRef:d,onBeforeLeaveRef:f,triggerRef:p,handleAdd:m,activateTab:h,handleClose:g}=a(Y);return{trigger:p,mergedClosable:l(()=>{if(e.internalAddable)return!1;let{closable:t}=e;return t===void 0?i.value:t}),style:o,addStyle:s,tabClass:c,addTabClass:u,clsPrefix:t,value:n,type:r,handleClose(t){t.stopPropagation(),!e.disabled&&g(e.name)},activateTab(){if(e.disabled)return;if(e.internalAddable){m();return}let{name:t}=e,r=++d.id;if(t!==n.value){let{value:i}=f;i?Promise.resolve(i(e.name,n.value)).then(e=>{e&&d.id===r&&h(t)}):h(t)}}}},render(){let{internalAddable:t,clsPrefix:r,name:i,disabled:a,label:o,tab:s,value:c,mergedClosable:l,trigger:u,$slots:{default:d}}=this,f=o??s;return n(`div`,{class:`${r}-tabs-tab-wrapper`},this.internalLeftPadded?n(`div`,{class:`${r}-tabs-tab-pad`}):null,n(`div`,Object.assign({key:i,"data-name":i,"data-disabled":a?!0:void 0},e({class:[`${r}-tabs-tab`,c===i&&`${r}-tabs-tab--active`,a&&`${r}-tabs-tab--disabled`,l&&`${r}-tabs-tab--closable`,t&&`${r}-tabs-tab--addable`,t?this.addTabClass:this.tabClass],onClick:u===`click`?this.activateTab:void 0,onMouseenter:u===`hover`?this.activateTab:void 0,style:t?this.addStyle:this.style},this.internalCreatedByPane?this.tabProps||{}:this.$attrs)),n(`span`,{class:`${r}-tabs-tab__label`},t?n(p,null,n(`div`,{class:`${r}-tabs-tab__height-placeholder`},`\xA0`),n(ae,{clsPrefix:r},{default:()=>n(L,null)})):d?d():typeof f==`object`?f:z(f??i)),l&&this.type===`card`?n(R,{clsPrefix:r,class:`${r}-tabs-tab__close`,onClick:this.handleClose,disabled:a}):null))}}),be=E(`tabs`,`
 box-sizing: border-box;
 width: 100%;
 display: flex;
 flex-direction: column;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
`,[I(`segment-type`,[E(`tabs-rail`,[w(`&.transition-disabled`,[E(`tabs-capsule`,`
 transition: none;
 `)])])]),I(`top`,[E(`tab-pane`,`
 padding: var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left);
 `)]),I(`left`,[E(`tab-pane`,`
 padding: var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left) var(--n-pane-padding-top);
 `)]),I(`left, right`,`
 flex-direction: row;
 `,[E(`tabs-bar`,`
 width: 2px;
 right: 0;
 transition:
 top .2s var(--n-bezier),
 max-height .2s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `),E(`tabs-tab`,`
 padding: var(--n-tab-padding-vertical); 
 `)]),I(`right`,`
 flex-direction: row-reverse;
 `,[E(`tab-pane`,`
 padding: var(--n-pane-padding-left) var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom);
 `),E(`tabs-bar`,`
 left: 0;
 `)]),I(`bottom`,`
 flex-direction: column-reverse;
 justify-content: flex-end;
 `,[E(`tab-pane`,`
 padding: var(--n-pane-padding-bottom) var(--n-pane-padding-right) var(--n-pane-padding-top) var(--n-pane-padding-left);
 `),E(`tabs-bar`,`
 top: 0;
 `)]),E(`tabs-rail`,`
 position: relative;
 padding: 3px;
 border-radius: var(--n-tab-border-radius);
 width: 100%;
 background-color: var(--n-color-segment);
 transition: background-color .3s var(--n-bezier);
 display: flex;
 align-items: center;
 `,[E(`tabs-capsule`,`
 border-radius: var(--n-tab-border-radius);
 position: absolute;
 pointer-events: none;
 background-color: var(--n-tab-color-segment);
 box-shadow: 0 1px 3px 0 rgba(0, 0, 0, .08);
 transition: transform 0.3s var(--n-bezier);
 `),E(`tabs-tab-wrapper`,`
 flex-basis: 0;
 flex-grow: 1;
 display: flex;
 align-items: center;
 justify-content: center;
 `,[E(`tabs-tab`,`
 overflow: hidden;
 border-radius: var(--n-tab-border-radius);
 width: 100%;
 display: flex;
 align-items: center;
 justify-content: center;
 `,[I(`active`,`
 font-weight: var(--n-font-weight-strong);
 color: var(--n-tab-text-color-active);
 `),w(`&:hover`,`
 color: var(--n-tab-text-color-hover);
 `)])])]),I(`flex`,[E(`tabs-nav`,`
 width: 100%;
 position: relative;
 `,[E(`tabs-wrapper`,`
 width: 100%;
 `,[E(`tabs-tab`,`
 margin-right: 0;
 `)])])]),E(`tabs-nav`,`
 box-sizing: border-box;
 line-height: 1.5;
 display: flex;
 transition: border-color .3s var(--n-bezier);
 `,[O(`prefix, suffix`,`
 display: flex;
 align-items: center;
 `),O(`prefix`,`padding-right: 16px;`),O(`suffix`,`padding-left: 16px;`)]),I(`top, bottom`,[w(`>`,[E(`tabs-nav`,[E(`tabs-nav-scroll-wrapper`,[w(`&::before`,`
 top: 0;
 bottom: 0;
 left: 0;
 width: 20px;
 `),w(`&::after`,`
 top: 0;
 bottom: 0;
 right: 0;
 width: 20px;
 `),I(`shadow-start`,[w(`&::before`,`
 box-shadow: inset 10px 0 8px -8px rgba(0, 0, 0, .12);
 `)]),I(`shadow-end`,[w(`&::after`,`
 box-shadow: inset -10px 0 8px -8px rgba(0, 0, 0, .12);
 `)])])])])]),I(`left, right`,[E(`tabs-nav-scroll-content`,`
 flex-direction: column;
 `),w(`>`,[E(`tabs-nav`,[E(`tabs-nav-scroll-wrapper`,[w(`&::before`,`
 top: 0;
 left: 0;
 right: 0;
 height: 20px;
 `),w(`&::after`,`
 bottom: 0;
 left: 0;
 right: 0;
 height: 20px;
 `),I(`shadow-start`,[w(`&::before`,`
 box-shadow: inset 0 10px 8px -8px rgba(0, 0, 0, .12);
 `)]),I(`shadow-end`,[w(`&::after`,`
 box-shadow: inset 0 -10px 8px -8px rgba(0, 0, 0, .12);
 `)])])])])]),E(`tabs-nav-scroll-wrapper`,`
 flex: 1;
 position: relative;
 overflow: hidden;
 `,[E(`tabs-nav-y-scroll`,`
 height: 100%;
 width: 100%;
 overflow-y: auto; 
 scrollbar-width: none;
 `,[w(`&::-webkit-scrollbar, &::-webkit-scrollbar-track-piece, &::-webkit-scrollbar-thumb`,`
 width: 0;
 height: 0;
 display: none;
 `)]),w(`&::before, &::after`,`
 transition: box-shadow .3s var(--n-bezier);
 pointer-events: none;
 content: "";
 position: absolute;
 z-index: 1;
 `)]),E(`tabs-nav-scroll-content`,`
 display: flex;
 position: relative;
 min-width: 100%;
 min-height: 100%;
 width: fit-content;
 box-sizing: border-box;
 `),E(`tabs-wrapper`,`
 display: inline-flex;
 flex-wrap: nowrap;
 position: relative;
 `),E(`tabs-tab-wrapper`,`
 display: flex;
 flex-wrap: nowrap;
 flex-shrink: 0;
 flex-grow: 0;
 `),E(`tabs-tab`,`
 cursor: pointer;
 white-space: nowrap;
 flex-wrap: nowrap;
 display: inline-flex;
 align-items: center;
 color: var(--n-tab-text-color);
 font-size: var(--n-tab-font-size);
 background-clip: padding-box;
 padding: var(--n-tab-padding);
 transition:
 box-shadow .3s var(--n-bezier),
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[I(`disabled`,{cursor:`not-allowed`}),O(`close`,`
 margin-left: 6px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),O(`label`,`
 display: flex;
 align-items: center;
 z-index: 1;
 `)]),E(`tabs-bar`,`
 position: absolute;
 bottom: 0;
 height: 2px;
 border-radius: 1px;
 background-color: var(--n-bar-color);
 transition:
 left .2s var(--n-bezier),
 max-width .2s var(--n-bezier),
 opacity .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `,[w(`&.transition-disabled`,`
 transition: none;
 `),I(`disabled`,`
 background-color: var(--n-tab-text-color-disabled)
 `)]),E(`tabs-pane-wrapper`,`
 position: relative;
 overflow: hidden;
 transition: max-height .2s var(--n-bezier);
 `),E(`tab-pane`,`
 color: var(--n-pane-text-color);
 width: 100%;
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 opacity .2s var(--n-bezier);
 left: 0;
 right: 0;
 top: 0;
 `,[w(`&.next-transition-leave-active, &.prev-transition-leave-active, &.next-transition-enter-active, &.prev-transition-enter-active`,`
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 transform .2s var(--n-bezier),
 opacity .2s var(--n-bezier);
 `),w(`&.next-transition-leave-active, &.prev-transition-leave-active`,`
 position: absolute;
 `),w(`&.next-transition-enter-from, &.prev-transition-leave-to`,`
 transform: translateX(32px);
 opacity: 0;
 `),w(`&.next-transition-leave-to, &.prev-transition-enter-from`,`
 transform: translateX(-32px);
 opacity: 0;
 `),w(`&.next-transition-leave-from, &.next-transition-enter-to, &.prev-transition-leave-from, &.prev-transition-enter-to`,`
 transform: translateX(0);
 opacity: 1;
 `)]),E(`tabs-tab-pad`,`
 box-sizing: border-box;
 width: var(--n-tab-gap);
 flex-grow: 0;
 flex-shrink: 0;
 `),I(`line-type, bar-type`,[E(`tabs-tab`,`
 font-weight: var(--n-tab-font-weight);
 box-sizing: border-box;
 vertical-align: bottom;
 `,[w(`&:hover`,{color:`var(--n-tab-text-color-hover)`}),I(`active`,`
 color: var(--n-tab-text-color-active);
 font-weight: var(--n-tab-font-weight-active);
 `),I(`disabled`,{color:`var(--n-tab-text-color-disabled)`})])]),E(`tabs-nav`,[I(`line-type`,[I(`top`,[O(`prefix, suffix`,`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),E(`tabs-nav-scroll-content`,`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),E(`tabs-bar`,`
 bottom: -1px;
 `)]),I(`left`,[O(`prefix, suffix`,`
 border-right: 1px solid var(--n-tab-border-color);
 `),E(`tabs-nav-scroll-content`,`
 border-right: 1px solid var(--n-tab-border-color);
 `),E(`tabs-bar`,`
 right: -1px;
 `)]),I(`right`,[O(`prefix, suffix`,`
 border-left: 1px solid var(--n-tab-border-color);
 `),E(`tabs-nav-scroll-content`,`
 border-left: 1px solid var(--n-tab-border-color);
 `),E(`tabs-bar`,`
 left: -1px;
 `)]),I(`bottom`,[O(`prefix, suffix`,`
 border-top: 1px solid var(--n-tab-border-color);
 `),E(`tabs-nav-scroll-content`,`
 border-top: 1px solid var(--n-tab-border-color);
 `),E(`tabs-bar`,`
 top: -1px;
 `)]),O(`prefix, suffix`,`
 transition: border-color .3s var(--n-bezier);
 `),E(`tabs-nav-scroll-content`,`
 transition: border-color .3s var(--n-bezier);
 `),E(`tabs-bar`,`
 border-radius: 0;
 `)]),I(`card-type`,[O(`prefix, suffix`,`
 transition: border-color .3s var(--n-bezier);
 `),E(`tabs-pad`,`
 flex-grow: 1;
 transition: border-color .3s var(--n-bezier);
 `),E(`tabs-tab-pad`,`
 transition: border-color .3s var(--n-bezier);
 `),E(`tabs-tab`,`
 font-weight: var(--n-tab-font-weight);
 border: 1px solid var(--n-tab-border-color);
 background-color: var(--n-tab-color);
 box-sizing: border-box;
 position: relative;
 vertical-align: bottom;
 display: flex;
 justify-content: space-between;
 font-size: var(--n-tab-font-size);
 color: var(--n-tab-text-color);
 `,[I(`addable`,`
 padding-left: 8px;
 padding-right: 8px;
 font-size: 16px;
 justify-content: center;
 `,[O(`height-placeholder`,`
 width: 0;
 font-size: var(--n-tab-font-size);
 `),b(`disabled`,[w(`&:hover`,`
 color: var(--n-tab-text-color-hover);
 `)])]),I(`closable`,`padding-right: 8px;`),I(`active`,`
 background-color: #0000;
 font-weight: var(--n-tab-font-weight-active);
 color: var(--n-tab-text-color-active);
 `),I(`disabled`,`color: var(--n-tab-text-color-disabled);`)])]),I(`left, right`,`
 flex-direction: column; 
 `,[O(`prefix, suffix`,`
 padding: var(--n-tab-padding-vertical);
 `),E(`tabs-wrapper`,`
 flex-direction: column;
 `),E(`tabs-tab-wrapper`,`
 flex-direction: column;
 `,[E(`tabs-tab-pad`,`
 height: var(--n-tab-gap-vertical);
 width: 100%;
 `)])]),I(`top`,[I(`card-type`,[E(`tabs-scroll-padding`,`border-bottom: 1px solid var(--n-tab-border-color);`),O(`prefix, suffix`,`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),E(`tabs-tab`,`
 border-top-left-radius: var(--n-tab-border-radius);
 border-top-right-radius: var(--n-tab-border-radius);
 `,[I(`active`,`
 border-bottom: 1px solid #0000;
 `)]),E(`tabs-tab-pad`,`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),E(`tabs-pad`,`
 border-bottom: 1px solid var(--n-tab-border-color);
 `)])]),I(`left`,[I(`card-type`,[E(`tabs-scroll-padding`,`border-right: 1px solid var(--n-tab-border-color);`),O(`prefix, suffix`,`
 border-right: 1px solid var(--n-tab-border-color);
 `),E(`tabs-tab`,`
 border-top-left-radius: var(--n-tab-border-radius);
 border-bottom-left-radius: var(--n-tab-border-radius);
 `,[I(`active`,`
 border-right: 1px solid #0000;
 `)]),E(`tabs-tab-pad`,`
 border-right: 1px solid var(--n-tab-border-color);
 `),E(`tabs-pad`,`
 border-right: 1px solid var(--n-tab-border-color);
 `)])]),I(`right`,[I(`card-type`,[E(`tabs-scroll-padding`,`border-left: 1px solid var(--n-tab-border-color);`),O(`prefix, suffix`,`
 border-left: 1px solid var(--n-tab-border-color);
 `),E(`tabs-tab`,`
 border-top-right-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[I(`active`,`
 border-left: 1px solid #0000;
 `)]),E(`tabs-tab-pad`,`
 border-left: 1px solid var(--n-tab-border-color);
 `),E(`tabs-pad`,`
 border-left: 1px solid var(--n-tab-border-color);
 `)])]),I(`bottom`,[I(`card-type`,[E(`tabs-scroll-padding`,`border-top: 1px solid var(--n-tab-border-color);`),O(`prefix, suffix`,`
 border-top: 1px solid var(--n-tab-border-color);
 `),E(`tabs-tab`,`
 border-bottom-left-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[I(`active`,`
 border-top: 1px solid #0000;
 `)]),E(`tabs-tab-pad`,`
 border-top: 1px solid var(--n-tab-border-color);
 `),E(`tabs-pad`,`
 border-top: 1px solid var(--n-tab-border-color);
 `)])])])]),xe=ve,Se=m({name:`Tabs`,props:Object.assign(Object.assign({},ie.props),{value:[String,Number],defaultValue:[String,Number],trigger:{type:String,default:`click`},type:{type:String,default:`bar`},closable:Boolean,justifyContent:String,size:String,placement:{type:String,default:`top`},tabStyle:[String,Object],tabClass:String,addTabStyle:[String,Object],addTabClass:String,barWidth:Number,paneClass:String,paneStyle:[String,Object],paneWrapperClass:String,paneWrapperStyle:[String,Object],addable:[Boolean,Object],tabsPadding:{type:Number,default:0},animated:Boolean,onBeforeLeave:Function,onAdd:Function,"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],onClose:[Function,Array],labelSize:String,activeName:[String,Number],onActiveNameChange:[Function,Array]}),slots:Object,setup(e,{slots:n}){let{mergedClsPrefixRef:a,inlineThemeDisabled:s,mergedComponentPropsRef:d}=C(e),p=ie(`Tabs`,`-tabs`,be,ce,e,a),m=f(null),h=f(null),g=f(null),_=f(null),v=f(null),b=f(null),x=f(!0),w=f(!0),E=ee(e,[`labelSize`,`size`]),D=l(()=>E.value?E.value:d?.value?.Tabs?.size||`medium`),O=ee(e,[`activeName`,`value`]),k=f(O.value??e.defaultValue??(n.default?T(n.default())[0]?.props?.name:null)),j=re(O,k),N={id:0},te=l(()=>{if(!(!e.justifyContent||e.type===`card`))return{display:`flex`,justifyContent:e.justifyContent}});i(j,()=>{N.id=0,L(),se()});function F(){let{value:e}=j;return e===null?null:m.value?.querySelector(`[data-name="${e}"]`)}function ne(t){if(e.type===`card`)return;let{value:n}=h;if(!n)return;let r=n.style.opacity===`0`;if(t){let i=`${a.value}-tabs-bar--disabled`,{barWidth:o,placement:s}=e;if(t.dataset.disabled===`true`?n.classList.add(i):n.classList.remove(i),[`top`,`bottom`].includes(s)){if(I([`top`,`maxHeight`,`height`]),typeof o==`number`&&t.offsetWidth>=o){let e=Math.floor((t.offsetWidth-o)/2)+t.offsetLeft;n.style.left=`${e}px`,n.style.maxWidth=`${o}px`}else n.style.left=`${t.offsetLeft}px`,n.style.maxWidth=`${t.offsetWidth}px`;n.style.width=`8192px`,r&&(n.style.transition=`none`),n.offsetWidth,r&&(n.style.transition=``,n.style.opacity=`1`)}else{if(I([`left`,`maxWidth`,`width`]),typeof o==`number`&&t.offsetHeight>=o){let e=Math.floor((t.offsetHeight-o)/2)+t.offsetTop;n.style.top=`${e}px`,n.style.maxHeight=`${o}px`}else n.style.top=`${t.offsetTop}px`,n.style.maxHeight=`${t.offsetHeight}px`;n.style.height=`8192px`,r&&(n.style.transition=`none`),n.offsetHeight,r&&(n.style.transition=``,n.style.opacity=`1`)}}}function ae(){if(e.type===`card`)return;let{value:t}=h;t&&(t.style.opacity=`0`)}function I(e){let{value:t}=h;if(t)for(let n of e)t.style[n]=``}function L(){if(e.type===`card`)return;let t=F();t?ne(t):ae()}function se(){let e=v.value?.$el;if(!e)return;let t=F();if(!t)return;let{scrollLeft:n,offsetWidth:r}=e,{offsetLeft:i,offsetWidth:a}=t;n>i?e.scrollTo({top:0,left:i,behavior:`smooth`}):i+a>n+r&&e.scrollTo({top:0,left:i+a-r,behavior:`smooth`})}let R=f(null),z=0,B=null;function le(e){let t=R.value;if(t){z=e.getBoundingClientRect().height;let n=`${z}px`,r=()=>{t.style.height=n,t.style.maxHeight=n};B?(r(),B(),B=null):B=r}}function ue(e){let t=R.value;if(t){let n=e.getBoundingClientRect().height,r=()=>{document.body.offsetHeight,t.style.maxHeight=`${n}px`,t.style.height=`${Math.max(z,n)}px`};B?(B(),B=null,r()):B=r}}function de(){let t=R.value;if(t){t.style.maxHeight=``,t.style.height=``;let{paneWrapperStyle:n}=e;if(typeof n==`string`)t.style.cssText=n;else if(n){let{maxHeight:e,height:r}=n;e!==void 0&&(t.style.maxHeight=e),r!==void 0&&(t.style.height=r)}}}let V={value:[]},H=f(`next`);function U(e){let t=j.value,n=`next`;for(let r of V.value){if(r===t)break;if(r===e){n=`prev`;break}}H.value=n,fe(e)}function fe(t){let{onActiveNameChange:n,onUpdateValue:r,"onUpdate:value":i}=e;n&&P(n,t),r&&P(r,t),i&&P(i,t),k.value=t}function pe(t){let{onClose:n}=e;n&&P(n,t)}let W=!0;function G(){let{value:e}=h;if(!e)return;W||=!1;let t=`transition-disabled`;e.classList.add(t),L(),e.classList.remove(t)}let K=f(null);function q({transitionDisabled:e}){let t=m.value;if(!t)return;e&&t.classList.add(`transition-disabled`);let n=F();n&&K.value&&(K.value.style.width=`${n.offsetWidth}px`,K.value.style.height=`${n.offsetHeight}px`,K.value.style.transform=`translateX(${n.offsetLeft-y(getComputedStyle(t).paddingLeft)}px)`,e&&K.value.offsetWidth),e&&t.classList.remove(`transition-disabled`)}i([j],()=>{e.type===`segment`&&u(()=>{q({transitionDisabled:!1})})}),r(()=>{e.type===`segment`&&q({transitionDisabled:!0})});let me=0;function he(t){if(t.contentRect.width===0&&t.contentRect.height===0||me===t.contentRect.width)return;me=t.contentRect.width;let{type:n}=e;if((n===`line`||n===`bar`)&&(W||e.justifyContent?.startsWith(`space`))&&G(),n!==`segment`){let{placement:t}=e;X((t===`top`||t===`bottom`?v.value?.$el:b.value)||null)}}let ge=xe(he,64);i([()=>e.justifyContent,()=>e.size],()=>{u(()=>{let{type:t}=e;(t===`line`||t===`bar`)&&G()})});let J=f(!1);function _e(t){let{target:n,contentRect:{width:r,height:i}}=t,a=n.parentElement.parentElement.offsetWidth,o=n.parentElement.parentElement.offsetHeight,{placement:s}=e;if(!J.value)s===`top`||s===`bottom`?a<r&&(J.value=!0):o<i&&(J.value=!0);else{let{value:e}=_;if(!e)return;s===`top`||s===`bottom`?a-r>e.$el.offsetWidth&&(J.value=!1):o-i>e.$el.offsetHeight&&(J.value=!1)}X(v.value?.$el||null)}let ve=xe(_e,64);function ye(){let{onAdd:t}=e;t&&t(),u(()=>{let e=F(),{value:t}=v;!e||!t||t.scrollTo({left:e.offsetLeft,top:0,behavior:`smooth`})})}function X(t){if(!t)return;let{placement:n}=e;if(n===`top`||n===`bottom`){let{scrollLeft:e,scrollWidth:n,offsetWidth:r}=t;x.value=e<=0,w.value=e+r>=n}else{let{scrollTop:e,scrollHeight:n,offsetHeight:r}=t;x.value=e<=0,w.value=e+r>=n}}let Z=xe(e=>{X(e.target)},64);t(Y,{triggerRef:c(e,`trigger`),tabStyleRef:c(e,`tabStyle`),tabClassRef:c(e,`tabClass`),addTabStyleRef:c(e,`addTabStyle`),addTabClassRef:c(e,`addTabClass`),paneClassRef:c(e,`paneClass`),paneStyleRef:c(e,`paneStyle`),mergedClsPrefixRef:a,typeRef:c(e,`type`),closableRef:c(e,`closable`),valueRef:j,tabChangeIdRef:N,onBeforeLeaveRef:c(e,`onBeforeLeave`),activateTab:U,handleClose:pe,handleAdd:ye}),oe(()=>{L(),se()}),o(()=>{let{value:e}=g;if(!e)return;let{value:t}=a,n=`${t}-tabs-nav-scroll-wrapper--shadow-start`,r=`${t}-tabs-nav-scroll-wrapper--shadow-end`;x.value?e.classList.remove(n):e.classList.add(n),w.value?e.classList.remove(r):e.classList.add(r)});let Se={syncBarPosition:()=>{L()}},Ce=()=>{q({transitionDisabled:!0})},Q=l(()=>{let{value:t}=D,{type:n}=e,r=`${t}${{card:`Card`,bar:`Bar`,line:`Line`,segment:`Segment`}[n]}`,{self:{barColor:i,closeIconColor:a,closeIconColorHover:o,closeIconColorPressed:s,tabColor:c,tabBorderColor:l,paneTextColor:u,tabFontWeight:d,tabBorderRadius:f,tabFontWeightActive:m,colorSegment:h,fontWeightStrong:g,tabColorSegment:_,closeSize:v,closeIconSize:y,closeColorHover:b,closeColorPressed:x,closeBorderRadius:S,[A(`panePadding`,t)]:C,[A(`tabPadding`,r)]:w,[A(`tabPaddingVertical`,r)]:T,[A(`tabGap`,r)]:E,[A(`tabGap`,`${r}Vertical`)]:O,[A(`tabTextColor`,n)]:k,[A(`tabTextColorActive`,n)]:j,[A(`tabTextColorHover`,n)]:ee,[A(`tabTextColorDisabled`,n)]:N,[A(`tabFontSize`,t)]:te},common:{cubicBezierEaseInOut:P}}=p.value;return{"--n-bezier":P,"--n-color-segment":h,"--n-bar-color":i,"--n-tab-font-size":te,"--n-tab-text-color":k,"--n-tab-text-color-active":j,"--n-tab-text-color-disabled":N,"--n-tab-text-color-hover":ee,"--n-pane-text-color":u,"--n-tab-border-color":l,"--n-tab-border-radius":f,"--n-close-size":v,"--n-close-icon-size":y,"--n-close-color-hover":b,"--n-close-color-pressed":x,"--n-close-border-radius":S,"--n-close-icon-color":a,"--n-close-icon-color-hover":o,"--n-close-icon-color-pressed":s,"--n-tab-color":c,"--n-tab-font-weight":d,"--n-tab-font-weight-active":m,"--n-tab-padding":w,"--n-tab-padding-vertical":T,"--n-tab-gap":E,"--n-tab-gap-vertical":O,"--n-pane-padding-left":M(C,`left`),"--n-pane-padding-right":M(C,`right`),"--n-pane-padding-top":M(C,`top`),"--n-pane-padding-bottom":M(C,`bottom`),"--n-font-weight-strong":g,"--n-tab-color-segment":_}}),$=s?S(`tabs`,l(()=>`${D.value[0]}${e.type[0]}`),Q,e):void 0;return Object.assign({mergedClsPrefix:a,mergedValue:j,renderedNames:new Set,segmentCapsuleElRef:K,tabsPaneWrapperRef:R,tabsElRef:m,barElRef:h,addTabInstRef:_,xScrollInstRef:v,scrollWrapperElRef:g,addTabFixed:J,tabWrapperStyle:te,handleNavResize:ge,mergedSize:D,handleScroll:Z,handleTabsResize:ve,cssVars:s?void 0:Q,themeClass:$?.themeClass,animationDirection:H,renderNameListRef:V,yScrollElRef:b,handleSegmentResize:Ce,onAnimationBeforeLeave:le,onAnimationEnter:ue,onAnimationAfterEnter:de,onRender:$?.onRender},Se)},render(){let{mergedClsPrefix:e,type:t,placement:r,addTabFixed:i,addable:a,mergedSize:o,renderNameListRef:s,onRender:c,paneWrapperClass:l,paneWrapperStyle:u,$slots:{default:d,prefix:f,suffix:p}}=this;c?.();let m=d?T(d()).filter(e=>e.type.__TAB_PANE__===!0):[],h=d?T(d()).filter(e=>e.type.__TAB__===!0):[],g=!h.length,_=t===`card`,v=t===`segment`,y=!_&&!v&&this.justifyContent;s.value=[];let b=()=>{let t=n(`div`,{style:this.tabWrapperStyle,class:`${e}-tabs-wrapper`},y?null:n(`div`,{class:`${e}-tabs-scroll-padding`,style:r===`top`||r===`bottom`?{width:`${this.tabsPadding}px`}:{height:`${this.tabsPadding}px`}}),g?m.map((e,t)=>(s.value.push(e.props.name),we(n(Z,Object.assign({},e.props,{internalCreatedByPane:!0,internalLeftPadded:t!==0&&(!y||y===`center`||y===`start`||y===`end`)}),e.children?{default:e.children.tab}:void 0)))):h.map((e,t)=>(s.value.push(e.props.name),we(t!==0&&!y?$(e):e))),!i&&a&&_?Q(a,(g?m.length:h.length)!==0):null,y?null:n(`div`,{class:`${e}-tabs-scroll-padding`,style:{width:`${this.tabsPadding}px`}}));return n(`div`,{ref:`tabsElRef`,class:`${e}-tabs-nav-scroll-content`},_&&a?n(j,{onResize:this.handleTabsResize},{default:()=>t}):t,_?n(`div`,{class:`${e}-tabs-pad`}):null,_?null:n(`div`,{ref:`barElRef`,class:`${e}-tabs-bar`}))},x=v?`top`:r;return n(`div`,{class:[`${e}-tabs`,this.themeClass,`${e}-tabs--${t}-type`,`${e}-tabs--${o}-size`,y&&`${e}-tabs--flex`,`${e}-tabs--${x}`],style:this.cssVars},n(`div`,{class:[`${e}-tabs-nav--${t}-type`,`${e}-tabs-nav--${x}`,`${e}-tabs-nav`]},k(f,t=>t&&n(`div`,{class:`${e}-tabs-nav__prefix`},t)),v?n(j,{onResize:this.handleSegmentResize},{default:()=>n(`div`,{class:`${e}-tabs-rail`,ref:`tabsElRef`},n(`div`,{class:`${e}-tabs-capsule`,ref:`segmentCapsuleElRef`},n(`div`,{class:`${e}-tabs-wrapper`},n(`div`,{class:`${e}-tabs-tab`}))),g?m.map((e,t)=>(s.value.push(e.props.name),n(Z,Object.assign({},e.props,{internalCreatedByPane:!0,internalLeftPadded:t!==0}),e.children?{default:e.children.tab}:void 0))):h.map((e,t)=>(s.value.push(e.props.name),t===0?e:$(e))))}):n(j,{onResize:this.handleNavResize},{default:()=>n(`div`,{class:`${e}-tabs-nav-scroll-wrapper`,ref:`scrollWrapperElRef`},[`top`,`bottom`].includes(x)?n(le,{ref:`xScrollInstRef`,onScroll:this.handleScroll},{default:b}):n(`div`,{class:`${e}-tabs-nav-y-scroll`,onScroll:this.handleScroll,ref:`yScrollElRef`},b()))}),i&&a&&_?Q(a,!0):null,k(p,t=>t&&n(`div`,{class:`${e}-tabs-nav__suffix`},t))),g&&(this.animated&&(x===`top`||x===`bottom`)?n(`div`,{ref:`tabsPaneWrapperRef`,style:u,class:[`${e}-tabs-pane-wrapper`,l]},Ce(m,this.mergedValue,this.renderedNames,this.onAnimationBeforeLeave,this.onAnimationEnter,this.onAnimationAfterEnter,this.animationDirection)):Ce(m,this.mergedValue,this.renderedNames)))}});function Ce(e,t,r,i,a,o,c){let l=[];return e.forEach(e=>{let{name:n,displayDirective:i,"display-directive":a}=e.props,o=e=>i===e||a===e,c=t===n;if(e.key!==void 0&&(e.key=n),c||o(`show`)||o(`show:lazy`)&&r.has(n)){r.has(n)||r.add(n);let t=!o(`if`);l.push(t?s(e,[[_,c]]):e)}}),c?n(g,{name:`${c}-transition`,onBeforeLeave:i,onEnter:a,onAfterEnter:o},{default:()=>l}):l}function Q(e,t){return n(Z,{ref:`addTabInstRef`,key:`__addable`,name:`__addable`,internalCreatedByPane:!0,internalAddable:!0,internalLeftPadded:t,disabled:typeof e==`object`&&e.disabled})}function $(e){let t=d(e);return t.props?t.props.internalLeftPadded=!0:t.props={internalLeftPadded:!0},t}function we(e){return Array.isArray(e.dynamicProps)?e.dynamicProps.includes(`internalLeftPadded`)||e.dynamicProps.push(`internalLeftPadded`):e.dynamicProps=[`internalLeftPadded`],e}export{X as n,Se as t};