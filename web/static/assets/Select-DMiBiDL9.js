import{A as e,B as t,D as n,F as r,H as i,I as a,J as o,M as s,O as c,P as l,Y as u,Z as d,at as f,h as p,j as m,tt as h,u as g,w as _}from"./request-BQhxbqbR.js";import{c as v,p as y,s as b}from"./use-message-DKxoS41w.js";import{$ as x,At as S,Bt as C,F as w,I as T,It as E,Lt as D,Mt as O,Nt as ee,P as k,Pt as A,Q as j,R as M,Rt as N,S as P,St as F,U as I,V as L,Vt as R,Y as z,Z as te,_ as B,_t as ne,at as V,c as H,ct as re,g as U,gt as ie,h as W,ht as G,jt as ae,l as K,mt as oe,nt as se,ot as q,q as J,r as Y,rt as ce,st as le,tt as ue,v as de,vt as fe,w as pe,x as X,y as Z,zt as Q}from"./light-B4JLqmyR.js";import{n as me}from"./Tooltip-C8CwNt1_.js";import{C as he,K as ge,S as _e,T as ve,U as ye,V as be,b as xe,d as Se,v as Ce,x as we,y as Te}from"./index-DUVLM3jR.js";function Ee(e){return e&-e}var De=class{constructor(e,t){this.l=e,this.min=t;let n=Array(e+1);for(let t=0;t<e+1;++t)n[t]=0;this.ft=n}add(e,t){if(t===0)return;let{l:n,ft:r}=this;for(e+=1;e<=n;)r[e]+=t,e+=Ee(e)}get(e){return this.sum(e+1)-this.sum(e)}sum(e){if(e===void 0&&(e=this.l),e<=0)return 0;let{ft:t,min:n,l:r}=this;if(e>r)throw Error("[FinweckTree.sum]: `i` is larger than length.");let i=e*n;for(;e>0;)i+=t[e],e-=Ee(e);return i}getBound(e){let t=0,n=this.l;for(;n>t;){let r=Math.floor((t+n)/2),i=this.sum(r);if(i>e){n=r;continue}else if(i<e){if(t===r)return this.sum(t+1)<=e?t+1:r;t=r}else return r}return t}},Oe;function ke(){return typeof document>`u`?!1:(Oe===void 0&&(Oe=`matchMedia`in window&&window.matchMedia(`(pointer:coarse)`).matches),Oe)}var Ae;function je(){return typeof document>`u`?1:(Ae===void 0&&(Ae=`chrome`in window?window.devicePixelRatio:1),Ae)}var Me=`VVirtualListXScroll`;function Ne({columnsRef:e,renderColRef:n,renderItemWithColsRef:r}){let i=h(0),a=h(0),o=p(()=>{let t=e.value;if(t.length===0)return null;let n=new De(t.length,0);return t.forEach((e,t)=>{n.add(t,e.width)}),n});return t(Me,{startIndexRef:F(()=>{let e=o.value;return e===null?0:Math.max(e.getBound(a.value)-1,0)}),endIndexRef:F(()=>{let t=o.value;return t===null?0:Math.min(t.getBound(a.value+i.value)+1,e.value.length-1)}),columnsRef:e,renderColRef:n,renderItemWithColsRef:r,getLeft:e=>{let t=o.value;return t===null?0:t.sum(e)}}),{listWidthRef:i,scrollLeftRef:a}}var Pe=_({name:`VirtualListRow`,props:{index:{type:Number,required:!0},item:{type:Object,required:!0}},setup(){let{startIndexRef:e,endIndexRef:t,columnsRef:n,getLeft:r,renderColRef:i,renderItemWithColsRef:a}=c(Me);return{startIndex:e,endIndex:t,columns:n,renderCol:i,renderItemWithCols:a,getLeft:r}},render(){let{startIndex:e,endIndex:t,columns:n,renderCol:r,renderItemWithCols:i,getLeft:a,item:o}=this;if(i!=null)return i({itemIndex:this.index,startColIndex:e,endColIndex:t,allColumns:n,item:o,getLeft:a});if(r!=null){let i=[];for(let s=e;s<=t;++s){let e=n[s];i.push(r({column:e,left:a(s),item:o}))}return i}return null}}),Fe=ue(`.v-vl`,{maxHeight:`inherit`,height:`100%`,overflow:`auto`,minWidth:`1px`},[ue(`&:not(.v-vl--show-scrollbar)`,{scrollbarWidth:`none`},[ue(`&::-webkit-scrollbar, &::-webkit-scrollbar-track-piece, &::-webkit-scrollbar-thumb`,{width:0,height:0,display:`none`})])]),Ie=_({name:`VirtualList`,inheritAttrs:!1,props:{showScrollbar:{type:Boolean,default:!0},columns:{type:Array,default:()=>[]},renderCol:Function,renderItemWithCols:Function,items:{type:Array,default:()=>[]},itemSize:{type:Number,required:!0},itemResizable:Boolean,itemsStyle:[String,Object],visibleItemsTag:{type:[String,Object],default:`div`},visibleItemsProps:Object,ignoreItemResize:Boolean,onScroll:Function,onWheel:Function,onResize:Function,defaultScrollKey:[Number,String],defaultScrollIndex:Number,keyField:{type:String,default:`key`},paddingTop:{type:[Number,String],default:0},paddingBottom:{type:[Number,String],default:0}},setup(e){let t=ce();Fe.mount({id:`vueuc/virtual-list`,head:!0,anchorMetaName:se,ssr:t}),a(()=>{let{defaultScrollIndex:t,defaultScrollKey:n}=e;t==null?n!=null&&C({key:n}):C({index:t})});let n=!1,i=!1;s(()=>{if(n=!1,!i){i=!0;return}C({top:y.value,left:l.value})}),r(()=>{n=!0,i||=!0});let o=F(()=>{if(e.renderCol==null&&e.renderItemWithCols==null||e.columns.length===0)return;let t=0;return e.columns.forEach(e=>{t+=e.width}),t}),c=p(()=>{let t=new Map,{keyField:n}=e;return e.items.forEach((e,r)=>{t.set(e[n],r)}),t}),{scrollLeftRef:l,listWidthRef:u}=Ne({columnsRef:f(e,`columns`),renderColRef:f(e,`renderCol`),renderItemWithColsRef:f(e,`renderItemWithCols`)}),d=h(null),m=h(void 0),g=new Map,_=p(()=>{let{items:t,itemSize:n,keyField:r}=e,i=new De(t.length,n);return t.forEach((e,t)=>{let n=e[r],a=g.get(n);a!==void 0&&i.add(t,a)}),i}),v=h(0),y=h(0),b=F(()=>Math.max(_.value.getBound(y.value-S(e.paddingTop))-1,0)),x=p(()=>{let{value:t}=m;if(t===void 0)return[];let{items:n,itemSize:r}=e,i=b.value,a=Math.min(i+Math.ceil(t/r+1),n.length-1),o=[];for(let e=i;e<=a;++e)o.push(n[e]);return o}),C=(e,t)=>{if(typeof e==`number`){D(e,t,`auto`);return}let{left:n,top:r,index:i,key:a,position:o,behavior:s,debounce:l=!0}=e;if(n!==void 0||r!==void 0)D(n,r,s);else if(i!==void 0)E(i,s,l);else if(a!==void 0){let e=c.value.get(a);e!==void 0&&E(e,s,l)}else o===`bottom`?D(0,2**53-1,s):o===`top`&&D(0,0,s)},w,T=null;function E(t,n,r){let{value:i}=_,a=i.sum(t)+S(e.paddingTop);if(!r)d.value.scrollTo({left:0,top:a,behavior:n});else{w=t,T!==null&&window.clearTimeout(T),T=window.setTimeout(()=>{w=void 0,T=null},16);let{scrollTop:e,offsetHeight:r}=d.value;if(a>e){let o=i.get(t);a+o<=e+r||d.value.scrollTo({left:0,top:a+o-r,behavior:n})}else d.value.scrollTo({left:0,top:a,behavior:n})}}function D(e,t,n){d.value.scrollTo({left:e,top:t,behavior:n})}function ee(t,r){if(n||e.ignoreItemResize||L(r.target))return;let{value:i}=_,a=c.value.get(t),o=i.get(a),s=r.borderBoxSize?.[0]?.blockSize??r.contentRect.height;if(s===o)return;s-e.itemSize===0?g.delete(t):g.set(t,s-e.itemSize);let l=s-o;if(l===0)return;i.add(a,l);let u=d.value;if(u!=null){if(w===void 0){let e=i.sum(a);u.scrollTop>e&&u.scrollBy(0,l)}else(a<w||a===w&&s+i.sum(a)>u.scrollTop+u.offsetHeight)&&u.scrollBy(0,l);I()}v.value++}let k=!ke(),j=!1;function M(t){var n;(n=e.onScroll)==null||n.call(e,t),(!k||!j)&&I()}function N(t){var n;if((n=e.onWheel)==null||n.call(e,t),k){let e=d.value;if(e!=null){if(t.deltaX===0&&(e.scrollTop===0&&t.deltaY<=0||e.scrollTop+e.offsetHeight>=e.scrollHeight&&t.deltaY>=0))return;t.preventDefault(),e.scrollTop+=t.deltaY/je(),e.scrollLeft+=t.deltaX/je(),I(),j=!0,A(()=>{j=!1})}}}function P(t){if(n||L(t.target))return;if(e.renderCol==null&&e.renderItemWithCols==null){if(t.contentRect.height===m.value)return}else if(t.contentRect.height===m.value&&t.contentRect.width===u.value)return;m.value=t.contentRect.height,u.value=t.contentRect.width;let{onResize:r}=e;r!==void 0&&r(t)}function I(){let{value:e}=d;e!=null&&(y.value=e.scrollTop,l.value=e.scrollLeft)}function L(e){let t=e;for(;t!==null;){if(t.style.display===`none`)return!0;t=t.parentElement}return!1}return{listHeight:m,listStyle:{overflow:`auto`},keyToIndex:c,itemsStyle:p(()=>{let{itemResizable:t}=e,n=O(_.value.sum());return v.value,[e.itemsStyle,{boxSizing:`content-box`,width:O(o.value),height:t?``:n,minHeight:t?n:``,paddingTop:O(e.paddingTop),paddingBottom:O(e.paddingBottom)}]}),visibleItemsStyle:p(()=>(v.value,{transform:`translateY(${O(_.value.sum(b.value))})`})),viewportItems:x,listElRef:d,itemsElRef:h(null),scrollTo:C,handleListResize:P,handleListScroll:M,handleListWheel:N,handleItemResize:ee}},render(){let{itemResizable:t,keyField:r,keyToIndex:i,visibleItemsTag:a}=this;return n(te,{onResize:this.handleListResize},{default:()=>{var o;return n(`div`,e(this.$attrs,{class:[`v-vl`,this.showScrollbar&&`v-vl--show-scrollbar`],onScroll:this.handleListScroll,onWheel:this.handleListWheel,ref:`listElRef`}),[this.items.length===0?(o=this.$slots).empty?.call(o):n(`div`,{ref:`itemsElRef`,class:`v-vl-items`,style:this.itemsStyle},[n(a,Object.assign({class:`v-vl-visible-items`,style:this.visibleItemsStyle},this.visibleItemsProps),{default:()=>{let{renderCol:e,renderItemWithCols:a}=this;return this.viewportItems.map(o=>{let s=o[r],c=i.get(s),l=e==null?void 0:n(Pe,{index:c,item:o}),u=a==null?void 0:n(Pe,{index:c,item:o}),d=this.$slots.default({item:o,renderedCols:l,renderedItemWithCols:u,index:c})[0];return t?n(te,{key:s,onResize:e=>this.handleItemResize(s,e)},{default:()=>d}):(d.key=s,d)})}})])])}})}}),$=`v-hidden`,Le=ue(`[v-hidden]`,{display:`none!important`}),Re=_({name:`Overflow`,props:{getCounter:Function,getTail:Function,updateCounter:Function,onUpdateCount:Function,onUpdateOverflow:Function},setup(e,{slots:t}){let n=h(null),r=h(null);function i(i){let{value:a}=n,{getCounter:o,getTail:s}=e,c;if(c=o===void 0?r.value:o(),!a||!c)return;c.hasAttribute($)&&c.removeAttribute($);let{children:l}=a;if(i.showAllItemsBeforeCalculate)for(let e of l)e.hasAttribute($)&&e.removeAttribute($);let u=a.offsetWidth,d=[],f=t.tail?s?.():null,p=f?f.offsetWidth:0,m=!1,h=a.children.length-+!!t.tail;for(let t=0;t<h-1;++t){if(t<0)continue;let n=l[t];if(m){n.hasAttribute($)||n.setAttribute($,``);continue}else n.hasAttribute($)&&n.removeAttribute($);let r=n.offsetWidth;if(p+=r,d[t]=r,p>u){let{updateCounter:n}=e;for(let r=t;r>=0;--r){let i=h-1-r;n===void 0?c.textContent=`${i}`:n(i);let a=c.offsetWidth;if(p-=d[r],p+a<=u||r===0){m=!0,t=r-1,f&&(t===-1?(f.style.maxWidth=`${u-a}px`,f.style.boxSizing=`border-box`):f.style.maxWidth=``);let{onUpdateCount:n}=e;n&&n(i);break}}}}let{onUpdateOverflow:g}=e;m?g!==void 0&&g(!0):(g!==void 0&&g(!1),c.setAttribute($,``))}let o=ce();return Le.mount({id:`vueuc/overflow`,head:!0,anchorMetaName:se,ssr:o}),a(()=>i({showAllItemsBeforeCalculate:!1})),{selfRef:n,counterRef:r,sync:i}},render(){let{$slots:e}=this;return m(()=>this.sync({showAllItemsBeforeCalculate:!1})),n(`div`,{class:`v-overflow`,ref:`selfRef`},[i(e,`default`),e.counter?e.counter():n(`span`,{style:{display:`inline-block`},ref:`counterRef`}),e.tail?e.tail():null])}});function ze(e,t){t&&(a(()=>{let{value:n}=e;n&&j.registerHandler(n,t)}),o(e,(e,t)=>{t&&j.unregisterHandler(t)},{deep:!1}),l(()=>{let{value:t}=e;t&&j.unregisterHandler(t)}))}function Be(e){switch(typeof e){case`string`:return e||void 0;case`number`:return String(e);default:return}}function Ve(e){let t=e.filter(e=>e!==void 0);if(t.length!==0)return t.length===1?t[0]:t=>{e.forEach(e=>{e&&e(t)})}}var He=_({name:`Checkmark`,render(){return n(`svg`,{xmlns:`http://www.w3.org/2000/svg`,viewBox:`0 0 16 16`},n(`g`,{fill:`none`},n(`path`,{d:`M14.046 3.486a.75.75 0 0 1-.032 1.06l-7.93 7.474a.85.85 0 0 1-1.188-.022l-2.68-2.72a.75.75 0 1 1 1.068-1.053l2.234 2.267l7.468-7.038a.75.75 0 0 1 1.06.032z`,fill:`currentColor`})))}}),Ue=_({name:`ChevronDown`,render(){return n(`svg`,{viewBox:`0 0 16 16`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`},n(`path`,{d:`M3.14645 5.64645C3.34171 5.45118 3.65829 5.45118 3.85355 5.64645L8 9.79289L12.1464 5.64645C12.3417 5.45118 12.6583 5.45118 12.8536 5.64645C13.0488 5.84171 13.0488 6.15829 12.8536 6.35355L8.35355 10.8536C8.15829 11.0488 7.84171 11.0488 7.64645 10.8536L3.14645 6.35355C2.95118 6.15829 2.95118 5.84171 3.14645 5.64645Z`,fill:`currentColor`}))}}),We=B(`clear`,()=>n(`svg`,{viewBox:`0 0 16 16`,version:`1.1`,xmlns:`http://www.w3.org/2000/svg`},n(`g`,{stroke:`none`,"stroke-width":`1`,fill:`none`,"fill-rule":`evenodd`},n(`g`,{fill:`currentColor`,"fill-rule":`nonzero`},n(`path`,{d:`M8,2 C11.3137085,2 14,4.6862915 14,8 C14,11.3137085 11.3137085,14 8,14 C4.6862915,14 2,11.3137085 2,8 C2,4.6862915 4.6862915,2 8,2 Z M6.5343055,5.83859116 C6.33943736,5.70359511 6.07001296,5.72288026 5.89644661,5.89644661 L5.89644661,5.89644661 L5.83859116,5.9656945 C5.70359511,6.16056264 5.72288026,6.42998704 5.89644661,6.60355339 L5.89644661,6.60355339 L7.293,8 L5.89644661,9.39644661 L5.83859116,9.4656945 C5.70359511,9.66056264 5.72288026,9.92998704 5.89644661,10.1035534 L5.89644661,10.1035534 L5.9656945,10.1614088 C6.16056264,10.2964049 6.42998704,10.2771197 6.60355339,10.1035534 L6.60355339,10.1035534 L8,8.707 L9.39644661,10.1035534 L9.4656945,10.1614088 C9.66056264,10.2964049 9.92998704,10.2771197 10.1035534,10.1035534 L10.1035534,10.1035534 L10.1614088,10.0343055 C10.2964049,9.83943736 10.2771197,9.57001296 10.1035534,9.39644661 L10.1035534,9.39644661 L8.707,8 L10.1035534,6.60355339 L10.1614088,6.5343055 C10.2964049,6.33943736 10.2771197,6.07001296 10.1035534,5.89644661 L10.1035534,5.89644661 L10.0343055,5.83859116 C9.83943736,5.70359511 9.57001296,5.72288026 9.39644661,5.89644661 L9.39644661,5.89644661 L8,7.293 L6.60355339,5.89644661 Z`}))))),Ge=_({name:`Empty`,render(){return n(`svg`,{viewBox:`0 0 28 28`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`},n(`path`,{d:`M26 7.5C26 11.0899 23.0899 14 19.5 14C15.9101 14 13 11.0899 13 7.5C13 3.91015 15.9101 1 19.5 1C23.0899 1 26 3.91015 26 7.5ZM16.8536 4.14645C16.6583 3.95118 16.3417 3.95118 16.1464 4.14645C15.9512 4.34171 15.9512 4.65829 16.1464 4.85355L18.7929 7.5L16.1464 10.1464C15.9512 10.3417 15.9512 10.6583 16.1464 10.8536C16.3417 11.0488 16.6583 11.0488 16.8536 10.8536L19.5 8.20711L22.1464 10.8536C22.3417 11.0488 22.6583 11.0488 22.8536 10.8536C23.0488 10.6583 23.0488 10.3417 22.8536 10.1464L20.2071 7.5L22.8536 4.85355C23.0488 4.65829 23.0488 4.34171 22.8536 4.14645C22.6583 3.95118 22.3417 3.95118 22.1464 4.14645L19.5 6.79289L16.8536 4.14645Z`,fill:`currentColor`}),n(`path`,{d:`M25 22.75V12.5991C24.5572 13.0765 24.053 13.4961 23.5 13.8454V16H17.5L17.3982 16.0068C17.0322 16.0565 16.75 16.3703 16.75 16.75C16.75 18.2688 15.5188 19.5 14 19.5C12.4812 19.5 11.25 18.2688 11.25 16.75L11.2432 16.6482C11.1935 16.2822 10.8797 16 10.5 16H4.5V7.25C4.5 6.2835 5.2835 5.5 6.25 5.5H12.2696C12.4146 4.97463 12.6153 4.47237 12.865 4H6.25C4.45507 4 3 5.45507 3 7.25V22.75C3 24.5449 4.45507 26 6.25 26H21.75C23.5449 26 25 24.5449 25 22.75ZM4.5 22.75V17.5H9.81597L9.85751 17.7041C10.2905 19.5919 11.9808 21 14 21L14.215 20.9947C16.2095 20.8953 17.842 19.4209 18.184 17.5H23.5V22.75C23.5 23.7165 22.7165 24.5 21.75 24.5H6.25C5.2835 24.5 4.5 23.7165 4.5 22.75Z`,fill:`currentColor`}))}}),Ke=D(`base-clear`,`
 flex-shrink: 0;
 height: 1em;
 width: 1em;
 position: relative;
`,[E(`>`,[N(`clear`,`
 font-size: var(--n-clear-size);
 height: 1em;
 width: 1em;
 cursor: pointer;
 color: var(--n-clear-color);
 transition: color .3s var(--n-bezier);
 display: flex;
 `,[E(`&:hover`,`
 color: var(--n-clear-color-hover)!important;
 `),E(`&:active`,`
 color: var(--n-clear-color-pressed)!important;
 `)]),N(`placeholder`,`
 display: flex;
 `),N(`clear, placeholder`,`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 `,[U({originalTransform:`translateX(-50%) translateY(-50%)`,left:`50%`,top:`50%`})])])]),qe=_({name:`BaseClear`,props:{clsPrefix:{type:String,required:!0},show:Boolean,onClear:Function},setup(e){return P(`-base-clear`,Ke,f(e,`clsPrefix`)),{handleMouseDown(e){e.preventDefault()}}},render(){let{clsPrefix:e}=this;return n(`div`,{class:`${e}-base-clear`},n(de,null,{default:()=>{var t;return this.show?n(`div`,{key:`dismiss`,class:`${e}-base-clear__clear`,onClick:this.onClear,onMousedown:this.handleMouseDown,"data-clear":!0},L(this.$slots.icon,()=>[n(Z,{clsPrefix:e},{default:()=>n(We,null)})])):n(`div`,{key:`icon`,class:`${e}-base-clear__placeholder`},(t=this.$slots).placeholder?.call(t))}}))}}),Je=_({props:{onFocus:Function,onBlur:Function},setup(e){return()=>n(`div`,{style:`width: 0; height: 0`,tabindex:0,onFocus:e.onFocus,onBlur:e.onBlur})}}),Ye=D(`empty`,`
 display: flex;
 flex-direction: column;
 align-items: center;
 font-size: var(--n-font-size);
`,[N(`icon`,`
 width: var(--n-icon-size);
 height: var(--n-icon-size);
 font-size: var(--n-icon-size);
 line-height: var(--n-icon-size);
 color: var(--n-icon-color);
 transition:
 color .3s var(--n-bezier);
 `,[E(`+`,[N(`description`,`
 margin-top: 8px;
 `)])]),N(`description`,`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),N(`extra`,`
 text-align: center;
 transition: color .3s var(--n-bezier);
 margin-top: 12px;
 color: var(--n-extra-text-color);
 `)]),Xe=_({name:`Empty`,props:Object.assign(Object.assign({},X.props),{description:String,showDescription:{type:Boolean,default:!0},showIcon:{type:Boolean,default:!0},size:{type:String,default:`medium`},renderIcon:Function}),slots:Object,setup(e){let{mergedClsPrefixRef:t,inlineThemeDisabled:r,mergedComponentPropsRef:i}=T(e),a=X(`Empty`,`-empty`,Ye,we,e,t),{localeRef:o}=me(`Empty`),s=p(()=>e.description??i?.value?.Empty?.description),c=p(()=>i?.value?.Empty?.renderIcon||(()=>n(Ge,null))),l=p(()=>{let{size:t}=e,{common:{cubicBezierEaseInOut:n},self:{[R(`iconSize`,t)]:r,[R(`fontSize`,t)]:i,textColor:o,iconColor:s,extraTextColor:c}}=a.value;return{"--n-icon-size":r,"--n-font-size":i,"--n-bezier":n,"--n-text-color":o,"--n-icon-color":s,"--n-extra-text-color":c}}),u=r?w(`empty`,p(()=>{let t=``,{size:n}=e;return t+=n[0],t}),l,e):void 0;return{mergedClsPrefix:t,mergedRenderIcon:c,localizedDescription:p(()=>s.value||o.value.description),cssVars:r?void 0:l,themeClass:u?.themeClass,onRender:u?.onRender}},render(){let{$slots:e,mergedClsPrefix:t,onRender:r}=this;return r?.(),n(`div`,{class:[`${t}-empty`,this.themeClass],style:this.cssVars},this.showIcon?n(`div`,{class:`${t}-empty__icon`},e.icon?e.icon():n(Z,{clsPrefix:t},{default:this.mergedRenderIcon})):null,this.showDescription?n(`div`,{class:`${t}-empty__description`},e.default?e.default():this.localizedDescription):null,e.extra?n(`div`,{class:`${t}-empty__extra`},e.extra()):null)}}),Ze=_({name:`NBaseSelectGroupHeader`,props:{clsPrefix:{type:String,required:!0},tmNode:{type:Object,required:!0}},setup(){let{renderLabelRef:e,renderOptionRef:t,labelFieldRef:n,nodePropsRef:r}=c(G);return{labelField:n,nodeProps:r,renderLabel:e,renderOption:t}},render(){let{clsPrefix:e,renderLabel:t,renderOption:r,nodeProps:i,tmNode:{rawNode:a}}=this,o=i?.(a),s=t?t(a,!1):be(a[this.labelField],a,!1),c=n(`div`,Object.assign({},o,{class:[`${e}-base-select-group-header`,o?.class]}),s);return a.render?a.render({node:c,option:a}):r?r({node:c,option:a,selected:!1}):c}});function Qe(e,t){return n(v,{name:`fade-in-scale-up-transition`},{default:()=>e?n(Z,{clsPrefix:t,class:`${t}-base-select-option__check`},{default:()=>n(He)}):null})}var $e=_({name:`NBaseSelectOption`,props:{clsPrefix:{type:String,required:!0},tmNode:{type:Object,required:!0}},setup(e){let{valueRef:t,pendingTmNodeRef:n,multipleRef:r,valueSetRef:i,renderLabelRef:a,renderOptionRef:o,labelFieldRef:s,valueFieldRef:l,showCheckmarkRef:u,nodePropsRef:d,handleOptionClick:f,handleOptionMouseEnter:p}=c(G),m=F(()=>{let{value:t}=n;return t?e.tmNode.key===t.key:!1});function h(t){let{tmNode:n}=e;n.disabled||f(t,n)}function g(t){let{tmNode:n}=e;n.disabled||p(t,n)}function _(t){let{tmNode:n}=e,{value:r}=m;n.disabled||r||p(t,n)}return{multiple:r,isGrouped:F(()=>{let{tmNode:t}=e,{parent:n}=t;return n&&n.rawNode.type===`group`}),showCheckmark:u,nodeProps:d,isPending:m,isSelected:F(()=>{let{value:n}=t,{value:a}=r;if(n===null)return!1;let o=e.tmNode.rawNode[l.value];if(a){let{value:e}=i;return e.has(o)}else return n===o}),labelField:s,renderLabel:a,renderOption:o,handleMouseMove:_,handleMouseEnter:g,handleClick:h}},render(){let{clsPrefix:e,tmNode:{rawNode:t},isSelected:r,isPending:i,isGrouped:a,showCheckmark:o,nodeProps:s,renderOption:c,renderLabel:l,handleClick:u,handleMouseEnter:d,handleMouseMove:f}=this,p=Qe(r,e),m=l?[l(t,r),o&&p]:[be(t[this.labelField],t,r),o&&p],h=s?.(t),g=n(`div`,Object.assign({},h,{class:[`${e}-base-select-option`,t.class,h?.class,{[`${e}-base-select-option--disabled`]:t.disabled,[`${e}-base-select-option--selected`]:r,[`${e}-base-select-option--grouped`]:a,[`${e}-base-select-option--pending`]:i,[`${e}-base-select-option--show-checkmark`]:o}],style:[h?.style||``,t.style||``],onClick:Ve([u,h?.onClick]),onMouseenter:Ve([d,h?.onMouseenter]),onMousemove:Ve([f,h?.onMousemove])}),n(`div`,{class:`${e}-base-select-option__content`},m));return t.render?t.render({node:g,option:t,selected:r}):c?c({node:g,option:t,selected:r}):g}}),et=D(`base-select-menu`,`
 line-height: 1.5;
 outline: none;
 z-index: 0;
 position: relative;
 border-radius: var(--n-border-radius);
 transition:
 background-color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 background-color: var(--n-color);
`,[D(`scrollbar`,`
 max-height: var(--n-height);
 `),D(`virtual-list`,`
 max-height: var(--n-height);
 `),D(`base-select-option`,`
 min-height: var(--n-option-height);
 font-size: var(--n-option-font-size);
 display: flex;
 align-items: center;
 `,[N(`content`,`
 z-index: 1;
 white-space: nowrap;
 text-overflow: ellipsis;
 overflow: hidden;
 `)]),D(`base-select-group-header`,`
 min-height: var(--n-option-height);
 font-size: .93em;
 display: flex;
 align-items: center;
 `),D(`base-select-menu-option-wrapper`,`
 position: relative;
 width: 100%;
 `),N(`loading, empty`,`
 display: flex;
 padding: 12px 32px;
 flex: 1;
 justify-content: center;
 `),N(`loading`,`
 color: var(--n-loading-color);
 font-size: var(--n-loading-size);
 `),N(`header`,`
 padding: 8px var(--n-option-padding-left);
 font-size: var(--n-option-font-size);
 transition: 
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 border-bottom: 1px solid var(--n-action-divider-color);
 color: var(--n-action-text-color);
 `),N(`action`,`
 padding: 8px var(--n-option-padding-left);
 font-size: var(--n-option-font-size);
 transition: 
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 border-top: 1px solid var(--n-action-divider-color);
 color: var(--n-action-text-color);
 `),D(`base-select-group-header`,`
 position: relative;
 cursor: default;
 padding: var(--n-option-padding);
 color: var(--n-group-header-text-color);
 `),D(`base-select-option`,`
 cursor: pointer;
 position: relative;
 padding: var(--n-option-padding);
 transition:
 color .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 box-sizing: border-box;
 color: var(--n-option-text-color);
 opacity: 1;
 `,[Q(`show-checkmark`,`
 padding-right: calc(var(--n-option-padding-right) + 20px);
 `),E(`&::before`,`
 content: "";
 position: absolute;
 left: 4px;
 right: 4px;
 top: 0;
 bottom: 0;
 border-radius: var(--n-border-radius);
 transition: background-color .3s var(--n-bezier);
 `),E(`&:active`,`
 color: var(--n-option-text-color-pressed);
 `),Q(`grouped`,`
 padding-left: calc(var(--n-option-padding-left) * 1.5);
 `),Q(`pending`,[E(`&::before`,`
 background-color: var(--n-option-color-pending);
 `)]),Q(`selected`,`
 color: var(--n-option-text-color-active);
 `,[E(`&::before`,`
 background-color: var(--n-option-color-active);
 `),Q(`pending`,[E(`&::before`,`
 background-color: var(--n-option-color-active-pending);
 `)])]),Q(`disabled`,`
 cursor: not-allowed;
 `,[C(`selected`,`
 color: var(--n-option-text-color-disabled);
 `),Q(`selected`,`
 opacity: var(--n-option-opacity-disabled);
 `)]),N(`check`,`
 font-size: 16px;
 position: absolute;
 right: calc(var(--n-option-padding-right) - 4px);
 top: calc(50% - 7px);
 color: var(--n-option-check-color);
 transition: color .3s var(--n-bezier);
 `,[H({enterScale:`0.5`})])])]),tt=_({name:`InternalSelectMenu`,props:Object.assign(Object.assign({},X.props),{clsPrefix:{type:String,required:!0},scrollable:{type:Boolean,default:!0},treeMate:{type:Object,required:!0},multiple:Boolean,size:{type:String,default:`medium`},value:{type:[String,Number,Array],default:null},autoPending:Boolean,virtualScroll:{type:Boolean,default:!0},show:{type:Boolean,default:!0},labelField:{type:String,default:`label`},valueField:{type:String,default:`value`},loading:Boolean,focusable:Boolean,renderLabel:Function,renderOption:Function,nodeProps:Function,showCheckmark:{type:Boolean,default:!0},onMousedown:Function,onScroll:Function,onFocus:Function,onBlur:Function,onKeyup:Function,onKeydown:Function,onTabOut:Function,onMouseenter:Function,onMouseleave:Function,onResize:Function,resetMenuOnOptionsChange:{type:Boolean,default:!0},inlineThemeDisabled:Boolean,scrollbarProps:Object,onToggle:Function}),setup(e){let{mergedClsPrefixRef:n,mergedRtlRef:r,mergedComponentPropsRef:i}=T(e),s=pe(`InternalSelectMenu`,r,n),c=X(`InternalSelectMenu`,`-internal-select-menu`,et,xe,e,f(e,`clsPrefix`)),u=h(null),d=h(null),g=h(null),_=p(()=>e.treeMate.getFlattenedNodes()),v=p(()=>he(_.value)),y=h(null);function b(){let{treeMate:t}=e,n=null,{value:r}=e;r===null?n=t.getFirstAvailableNode():(n=e.multiple?t.getNode((r||[])[(r||[]).length-1]):t.getNode(r),(!n||n.disabled)&&(n=t.getFirstAvailableNode())),V(n||null)}function x(){let{value:t}=y;t&&!e.treeMate.getNode(t.key)&&(y.value=null)}let C;o(()=>e.show,t=>{t?C=o(()=>e.treeMate,()=>{e.resetMenuOnOptionsChange?(e.autoPending?b():x(),m(H)):x()},{immediate:!0}):C?.()},{immediate:!0}),l(()=>{C?.()});let E=p(()=>S(c.value.self[R(`optionHeight`,e.size)])),D=p(()=>ae(c.value.self[R(`padding`,e.size)])),O=p(()=>e.multiple&&Array.isArray(e.value)?new Set(e.value):new Set),ee=p(()=>{let e=_.value;return e&&e.length===0}),k=p(()=>i?.value?.Select?.renderEmpty);function A(t){let{onToggle:n}=e;n&&n(t)}function j(t){let{onScroll:n}=e;n&&n(t)}function M(e){var t;(t=g.value)==null||t.sync(),j(e)}function N(){var e;(e=g.value)==null||e.sync()}function P(){let{value:e}=y;return e||null}function F(e,t){t.disabled||V(t,!1)}function I(e,t){t.disabled||A(t)}function L(t){var n;ge(t,`action`)||(n=e.onKeyup)==null||n.call(e,t)}function z(t){var n;ge(t,`action`)||(n=e.onKeydown)==null||n.call(e,t)}function te(t){var n;(n=e.onMousedown)==null||n.call(e,t),!e.focusable&&t.preventDefault()}function B(){let{value:e}=y;e&&V(e.getNext({loop:!0}),!0)}function ne(){let{value:e}=y;e&&V(e.getPrev({loop:!0}),!0)}function V(e,t=!1){y.value=e,t&&H()}function H(){var t,n;let r=y.value;if(!r)return;let i=v.value(r.key);i!==null&&(e.virtualScroll?(t=d.value)==null||t.scrollTo({index:i}):(n=g.value)==null||n.scrollTo({index:i,elSize:E.value}))}function re(t){var n;u.value?.contains(t.target)&&((n=e.onFocus)==null||n.call(e,t))}function U(t){var n;u.value?.contains(t.relatedTarget)||(n=e.onBlur)==null||n.call(e,t)}t(G,{handleOptionMouseEnter:F,handleOptionClick:I,valueSetRef:O,pendingTmNodeRef:y,nodePropsRef:f(e,`nodeProps`),showCheckmarkRef:f(e,`showCheckmark`),multipleRef:f(e,`multiple`),valueRef:f(e,`value`),renderLabelRef:f(e,`renderLabel`),renderOptionRef:f(e,`renderOption`),labelFieldRef:f(e,`labelField`),valueFieldRef:f(e,`valueField`)}),t(oe,u),a(()=>{let{value:e}=g;e&&e.sync()});let ie=p(()=>{let{size:t}=e,{common:{cubicBezierEaseInOut:n},self:{height:r,borderRadius:i,color:a,groupHeaderTextColor:o,actionDividerColor:s,optionTextColorPressed:l,optionTextColor:u,optionTextColorDisabled:d,optionTextColorActive:f,optionOpacityDisabled:p,optionCheckColor:m,actionTextColor:h,optionColorPending:g,optionColorActive:_,loadingColor:v,loadingSize:y,optionColorActivePending:b,[R(`optionFontSize`,t)]:x,[R(`optionHeight`,t)]:S,[R(`optionPadding`,t)]:C}}=c.value;return{"--n-height":r,"--n-action-divider-color":s,"--n-action-text-color":h,"--n-bezier":n,"--n-border-radius":i,"--n-color":a,"--n-option-font-size":x,"--n-group-header-text-color":o,"--n-option-check-color":m,"--n-option-color-pending":g,"--n-option-color-active":_,"--n-option-color-active-pending":b,"--n-option-height":S,"--n-option-opacity-disabled":p,"--n-option-text-color":u,"--n-option-text-color-active":f,"--n-option-text-color-disabled":d,"--n-option-text-color-pressed":l,"--n-option-padding":C,"--n-option-padding-left":ae(C,`left`),"--n-option-padding-right":ae(C,`right`),"--n-loading-color":v,"--n-loading-size":y}}),{inlineThemeDisabled:W}=e,K=W?w(`internal-select-menu`,p(()=>e.size[0]),ie,e):void 0,se={selfRef:u,next:B,prev:ne,getPendingTmNode:P};return ze(u,e.onResize),Object.assign({mergedTheme:c,mergedClsPrefix:n,rtlEnabled:s,virtualListRef:d,scrollbarRef:g,itemSize:E,padding:D,flattenedNodes:_,empty:ee,mergedRenderEmpty:k,virtualListContainer(){let{value:e}=d;return e?.listElRef},virtualListContent(){let{value:e}=d;return e?.itemsElRef},doScroll:j,handleFocusin:re,handleFocusout:U,handleKeyUp:L,handleKeyDown:z,handleMouseDown:te,handleVirtualListResize:N,handleVirtualListScroll:M,cssVars:W?void 0:ie,themeClass:K?.themeClass,onRender:K?.onRender},se)},render(){let{$slots:e,virtualScroll:t,clsPrefix:r,mergedTheme:i,themeClass:a,onRender:o}=this;return o?.(),n(`div`,{ref:`selfRef`,tabindex:this.focusable?0:-1,class:[`${r}-base-select-menu`,`${r}-base-select-menu--${this.size}-size`,this.rtlEnabled&&`${r}-base-select-menu--rtl`,a,this.multiple&&`${r}-base-select-menu--multiple`],style:this.cssVars,onFocusin:this.handleFocusin,onFocusout:this.handleFocusout,onKeyup:this.handleKeyUp,onKeydown:this.handleKeyDown,onMousedown:this.handleMouseDown,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},I(e.header,e=>e&&n(`div`,{class:`${r}-base-select-menu__header`,"data-header":!0,key:`header`},e)),this.loading?n(`div`,{class:`${r}-base-select-menu__loading`},n(W,{clsPrefix:r,strokeWidth:20})):this.empty?n(`div`,{class:`${r}-base-select-menu__empty`,"data-empty":!0},L(e.empty,()=>[this.mergedRenderEmpty?.call(this)||n(Xe,{theme:i.peers.Empty,themeOverrides:i.peerOverrides.Empty,size:this.size})])):n(K,Object.assign({ref:`scrollbarRef`,theme:i.peers.Scrollbar,themeOverrides:i.peerOverrides.Scrollbar,scrollable:this.scrollable,container:t?this.virtualListContainer:void 0,content:t?this.virtualListContent:void 0,onScroll:t?void 0:this.doScroll},this.scrollbarProps),{default:()=>t?n(Ie,{ref:`virtualListRef`,class:`${r}-virtual-list`,items:this.flattenedNodes,itemSize:this.itemSize,showScrollbar:!1,paddingTop:this.padding.top,paddingBottom:this.padding.bottom,onResize:this.handleVirtualListResize,onScroll:this.handleVirtualListScroll,itemResizable:!0},{default:({item:e})=>e.isGroup?n(Ze,{key:e.key,clsPrefix:r,tmNode:e}):e.ignored?null:n($e,{clsPrefix:r,key:e.key,tmNode:e})}):n(`div`,{class:`${r}-base-select-menu-option-wrapper`,style:{paddingTop:this.padding.top,paddingBottom:this.padding.bottom}},this.flattenedNodes.map(e=>e.isGroup?n(Ze,{key:e.key,clsPrefix:r,tmNode:e}):n($e,{clsPrefix:r,key:e.key,tmNode:e})))}),I(e.action,e=>e&&[n(`div`,{class:`${r}-base-select-menu__action`,"data-action":!0,key:`action`},e),n(Je,{onFocus:this.onTabOut,key:`focus-detector`})]))}}),nt={color:Object,type:{type:String,default:`default`},round:Boolean,size:String,closable:Boolean,disabled:{type:Boolean,default:void 0}},rt=D(`tag`,`
 --n-close-margin: var(--n-close-margin-top) var(--n-close-margin-right) var(--n-close-margin-bottom) var(--n-close-margin-left);
 white-space: nowrap;
 position: relative;
 box-sizing: border-box;
 cursor: default;
 display: inline-flex;
 align-items: center;
 flex-wrap: nowrap;
 padding: var(--n-padding);
 border-radius: var(--n-border-radius);
 color: var(--n-text-color);
 background-color: var(--n-color);
 transition: 
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 line-height: 1;
 height: var(--n-height);
 font-size: var(--n-font-size);
`,[Q(`strong`,`
 font-weight: var(--n-font-weight-strong);
 `),N(`border`,`
 pointer-events: none;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
 border: var(--n-border);
 transition: border-color .3s var(--n-bezier);
 `),N(`icon`,`
 display: flex;
 margin: 0 4px 0 0;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 font-size: var(--n-avatar-size-override);
 `),N(`avatar`,`
 display: flex;
 margin: 0 6px 0 0;
 `),N(`close`,`
 margin: var(--n-close-margin);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),Q(`round`,`
 padding: 0 calc(var(--n-height) / 3);
 border-radius: calc(var(--n-height) / 2);
 `,[N(`icon`,`
 margin: 0 4px 0 calc((var(--n-height) - 8px) / -2);
 `),N(`avatar`,`
 margin: 0 6px 0 calc((var(--n-height) - 8px) / -2);
 `),Q(`closable`,`
 padding: 0 calc(var(--n-height) / 4) 0 calc(var(--n-height) / 3);
 `)]),Q(`icon, avatar`,[Q(`round`,`
 padding: 0 calc(var(--n-height) / 3) 0 calc(var(--n-height) / 2);
 `)]),Q(`disabled`,`
 cursor: not-allowed !important;
 opacity: var(--n-opacity-disabled);
 `),Q(`checkable`,`
 cursor: pointer;
 box-shadow: none;
 color: var(--n-text-color-checkable);
 background-color: var(--n-color-checkable);
 `,[C(`disabled`,[E(`&:hover`,`background-color: var(--n-color-hover-checkable);`,[C(`checked`,`color: var(--n-text-color-hover-checkable);`)]),E(`&:active`,`background-color: var(--n-color-pressed-checkable);`,[C(`checked`,`color: var(--n-text-color-pressed-checkable);`)])]),Q(`checked`,`
 color: var(--n-text-color-checked);
 background-color: var(--n-color-checked);
 `,[C(`disabled`,[E(`&:hover`,`background-color: var(--n-color-checked-hover);`),E(`&:active`,`background-color: var(--n-color-checked-pressed);`)])])])]),it=Object.assign(Object.assign(Object.assign({},X.props),nt),{bordered:{type:Boolean,default:void 0},checked:Boolean,checkable:Boolean,strong:Boolean,triggerClickOnClose:Boolean,onClose:[Array,Function],onMouseenter:Function,onMouseleave:Function,"onUpdate:checked":Function,onUpdateChecked:Function,internalCloseFocusable:{type:Boolean,default:!0},internalCloseIsButtonTag:{type:Boolean,default:!0},onCheckedChange:Function}),at=b(`n-tag`),ot=_({name:`Tag`,props:it,slots:Object,setup(e){let n=h(null),{mergedBorderedRef:r,mergedClsPrefixRef:i,inlineThemeDisabled:a,mergedRtlRef:o,mergedComponentPropsRef:s}=T(e),c=p(()=>e.size||s?.value?.Tag?.size||`medium`),l=X(`Tag`,`-tag`,rt,Te,e,i);t(at,{roundRef:f(e,`round`)});function u(){if(!e.disabled&&e.checkable){let{checked:t,onCheckedChange:n,onUpdateChecked:r,"onUpdate:checked":i}=e;r&&r(!t),i&&i(!t),n&&n(!t)}}function d(t){if(e.triggerClickOnClose||t.stopPropagation(),!e.disabled){let{onClose:n}=e;n&&J(n,t)}}let m={setTextContent(e){let{value:t}=n;t&&(t.textContent=e)}},g=pe(`Tag`,o,i),_=p(()=>{let{type:t,color:{color:n,textColor:i}={}}=e,a=c.value,{common:{cubicBezierEaseInOut:o},self:{padding:s,closeMargin:u,borderRadius:d,opacityDisabled:f,textColorCheckable:p,textColorHoverCheckable:m,textColorPressedCheckable:h,textColorChecked:g,colorCheckable:_,colorHoverCheckable:v,colorPressedCheckable:y,colorChecked:b,colorCheckedHover:x,colorCheckedPressed:S,closeBorderRadius:C,fontWeightStrong:w,[R(`colorBordered`,t)]:T,[R(`closeSize`,a)]:E,[R(`closeIconSize`,a)]:D,[R(`fontSize`,a)]:O,[R(`height`,a)]:ee,[R(`color`,t)]:k,[R(`textColor`,t)]:A,[R(`border`,t)]:j,[R(`closeIconColor`,t)]:M,[R(`closeIconColorHover`,t)]:N,[R(`closeIconColorPressed`,t)]:P,[R(`closeColorHover`,t)]:F,[R(`closeColorPressed`,t)]:I}}=l.value,L=ae(u);return{"--n-font-weight-strong":w,"--n-avatar-size-override":`calc(${ee} - 8px)`,"--n-bezier":o,"--n-border-radius":d,"--n-border":j,"--n-close-icon-size":D,"--n-close-color-pressed":I,"--n-close-color-hover":F,"--n-close-border-radius":C,"--n-close-icon-color":M,"--n-close-icon-color-hover":N,"--n-close-icon-color-pressed":P,"--n-close-icon-color-disabled":M,"--n-close-margin-top":L.top,"--n-close-margin-right":L.right,"--n-close-margin-bottom":L.bottom,"--n-close-margin-left":L.left,"--n-close-size":E,"--n-color":n||(r.value?T:k),"--n-color-checkable":_,"--n-color-checked":b,"--n-color-checked-hover":x,"--n-color-checked-pressed":S,"--n-color-hover-checkable":v,"--n-color-pressed-checkable":y,"--n-font-size":O,"--n-height":ee,"--n-opacity-disabled":f,"--n-padding":s,"--n-text-color":i||A,"--n-text-color-checkable":p,"--n-text-color-checked":g,"--n-text-color-hover-checkable":m,"--n-text-color-pressed-checkable":h}}),v=a?w(`tag`,p(()=>{let t=``,{type:n,color:{color:i,textColor:a}={}}=e;return t+=n[0],t+=c.value[0],i&&(t+=`a${z(i)}`),a&&(t+=`b${z(a)}`),r.value&&(t+=`c`),t}),_,e):void 0;return Object.assign(Object.assign({},m),{rtlEnabled:g,mergedClsPrefix:i,contentRef:n,mergedBordered:r,handleClick:u,handleCloseClick:d,cssVars:a?void 0:_,themeClass:v?.themeClass,onRender:v?.onRender})},render(){var e;let{mergedClsPrefix:t,rtlEnabled:r,closable:i,color:{borderColor:a}={},round:o,onRender:s,$slots:c}=this;s?.();let l=I(c.avatar,e=>e&&n(`div`,{class:`${t}-tag__avatar`},e)),u=I(c.icon,e=>e&&n(`div`,{class:`${t}-tag__icon`},e));return n(`div`,{class:[`${t}-tag`,this.themeClass,{[`${t}-tag--rtl`]:r,[`${t}-tag--strong`]:this.strong,[`${t}-tag--disabled`]:this.disabled,[`${t}-tag--checkable`]:this.checkable,[`${t}-tag--checked`]:this.checkable&&this.checked,[`${t}-tag--round`]:o,[`${t}-tag--avatar`]:l,[`${t}-tag--icon`]:u,[`${t}-tag--closable`]:i}],style:this.cssVars,onClick:this.handleClick,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},u||l,n(`span`,{class:`${t}-tag__content`,ref:`contentRef`},(e=this.$slots).default?.call(e)),!this.checkable&&i?n(ve,{clsPrefix:t,class:`${t}-tag__close`,disabled:this.disabled,onClick:this.handleCloseClick,focusable:this.internalCloseFocusable,round:o,isButtonTag:this.internalCloseIsButtonTag,absolute:!0}):null,!this.checkable&&this.mergedBordered?n(`div`,{class:`${t}-tag__border`,style:{borderColor:a}}):null)}}),st=_({name:`InternalSelectionSuffix`,props:{clsPrefix:{type:String,required:!0},showArrow:{type:Boolean,default:void 0},showClear:{type:Boolean,default:void 0},loading:{type:Boolean,default:!1},onClear:Function},setup(e,{slots:t}){return()=>{let{clsPrefix:r}=e;return n(W,{clsPrefix:r,class:`${r}-base-suffix`,strokeWidth:24,scale:.85,show:e.loading},{default:()=>e.showArrow?n(qe,{clsPrefix:r,show:e.showClear,onClear:e.onClear},{placeholder:()=>n(Z,{clsPrefix:r,class:`${r}-base-suffix__arrow`},{default:()=>L(t.default,()=>[n(Ue,null)])})}):null})}}}),ct=E([D(`base-selection`,`
 --n-padding-single: var(--n-padding-single-top) var(--n-padding-single-right) var(--n-padding-single-bottom) var(--n-padding-single-left);
 --n-padding-multiple: var(--n-padding-multiple-top) var(--n-padding-multiple-right) var(--n-padding-multiple-bottom) var(--n-padding-multiple-left);
 position: relative;
 z-index: auto;
 box-shadow: none;
 width: 100%;
 max-width: 100%;
 display: inline-block;
 vertical-align: bottom;
 border-radius: var(--n-border-radius);
 min-height: var(--n-height);
 line-height: 1.5;
 font-size: var(--n-font-size);
 `,[D(`base-loading`,`
 color: var(--n-loading-color);
 `),D(`base-selection-tags`,`min-height: var(--n-height);`),N(`border, state-border`,`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 pointer-events: none;
 border: var(--n-border);
 border-radius: inherit;
 transition:
 box-shadow .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `),N(`state-border`,`
 z-index: 1;
 border-color: #0000;
 `),D(`base-suffix`,`
 cursor: pointer;
 position: absolute;
 top: 50%;
 transform: translateY(-50%);
 right: 10px;
 `,[N(`arrow`,`
 font-size: var(--n-arrow-size);
 color: var(--n-arrow-color);
 transition: color .3s var(--n-bezier);
 `)]),D(`base-selection-overlay`,`
 display: flex;
 align-items: center;
 white-space: nowrap;
 pointer-events: none;
 position: absolute;
 top: 0;
 right: 0;
 bottom: 0;
 left: 0;
 padding: var(--n-padding-single);
 transition: color .3s var(--n-bezier);
 `,[N(`wrapper`,`
 flex-basis: 0;
 flex-grow: 1;
 overflow: hidden;
 text-overflow: ellipsis;
 `)]),D(`base-selection-placeholder`,`
 color: var(--n-placeholder-color);
 `,[N(`inner`,`
 max-width: 100%;
 overflow: hidden;
 `)]),D(`base-selection-tags`,`
 cursor: pointer;
 outline: none;
 box-sizing: border-box;
 position: relative;
 z-index: auto;
 display: flex;
 padding: var(--n-padding-multiple);
 flex-wrap: wrap;
 align-items: center;
 width: 100%;
 vertical-align: bottom;
 background-color: var(--n-color);
 border-radius: inherit;
 transition:
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `),D(`base-selection-label`,`
 height: var(--n-height);
 display: inline-flex;
 width: 100%;
 vertical-align: bottom;
 cursor: pointer;
 outline: none;
 z-index: auto;
 box-sizing: border-box;
 position: relative;
 transition:
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 border-radius: inherit;
 background-color: var(--n-color);
 align-items: center;
 `,[D(`base-selection-input`,`
 font-size: inherit;
 line-height: inherit;
 outline: none;
 cursor: pointer;
 box-sizing: border-box;
 border:none;
 width: 100%;
 padding: var(--n-padding-single);
 background-color: #0000;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 caret-color: var(--n-caret-color);
 `,[N(`content`,`
 text-overflow: ellipsis;
 overflow: hidden;
 white-space: nowrap; 
 `)]),N(`render-label`,`
 color: var(--n-text-color);
 `)]),C(`disabled`,[E(`&:hover`,[N(`state-border`,`
 box-shadow: var(--n-box-shadow-hover);
 border: var(--n-border-hover);
 `)]),Q(`focus`,[N(`state-border`,`
 box-shadow: var(--n-box-shadow-focus);
 border: var(--n-border-focus);
 `)]),Q(`active`,[N(`state-border`,`
 box-shadow: var(--n-box-shadow-active);
 border: var(--n-border-active);
 `),D(`base-selection-label`,`background-color: var(--n-color-active);`),D(`base-selection-tags`,`background-color: var(--n-color-active);`)])]),Q(`disabled`,`cursor: not-allowed;`,[N(`arrow`,`
 color: var(--n-arrow-color-disabled);
 `),D(`base-selection-label`,`
 cursor: not-allowed;
 background-color: var(--n-color-disabled);
 `,[D(`base-selection-input`,`
 cursor: not-allowed;
 color: var(--n-text-color-disabled);
 `),N(`render-label`,`
 color: var(--n-text-color-disabled);
 `)]),D(`base-selection-tags`,`
 cursor: not-allowed;
 background-color: var(--n-color-disabled);
 `),D(`base-selection-placeholder`,`
 cursor: not-allowed;
 color: var(--n-placeholder-color-disabled);
 `)]),D(`base-selection-input-tag`,`
 height: calc(var(--n-height) - 6px);
 line-height: calc(var(--n-height) - 6px);
 outline: none;
 display: none;
 position: relative;
 margin-bottom: 3px;
 max-width: 100%;
 vertical-align: bottom;
 `,[N(`input`,`
 font-size: inherit;
 font-family: inherit;
 min-width: 1px;
 padding: 0;
 background-color: #0000;
 outline: none;
 border: none;
 max-width: 100%;
 overflow: hidden;
 width: 1em;
 line-height: inherit;
 cursor: pointer;
 color: var(--n-text-color);
 caret-color: var(--n-caret-color);
 `),N(`mirror`,`
 position: absolute;
 left: 0;
 top: 0;
 white-space: pre;
 visibility: hidden;
 user-select: none;
 -webkit-user-select: none;
 opacity: 0;
 `)]),[`warning`,`error`].map(e=>Q(`${e}-status`,[N(`state-border`,`border: var(--n-border-${e});`),C(`disabled`,[E(`&:hover`,[N(`state-border`,`
 box-shadow: var(--n-box-shadow-hover-${e});
 border: var(--n-border-hover-${e});
 `)]),Q(`active`,[N(`state-border`,`
 box-shadow: var(--n-box-shadow-active-${e});
 border: var(--n-border-active-${e});
 `),D(`base-selection-label`,`background-color: var(--n-color-active-${e});`),D(`base-selection-tags`,`background-color: var(--n-color-active-${e});`)]),Q(`focus`,[N(`state-border`,`
 box-shadow: var(--n-box-shadow-focus-${e});
 border: var(--n-border-focus-${e});
 `)])])]))]),D(`base-selection-popover`,`
 margin-bottom: -3px;
 display: flex;
 flex-wrap: wrap;
 margin-right: -8px;
 `),D(`base-selection-tag-wrapper`,`
 max-width: 100%;
 display: inline-flex;
 padding: 0 7px 3px 0;
 `,[E(`&:last-child`,`padding-right: 0;`),D(`tag`,`
 font-size: 14px;
 max-width: 100%;
 `,[N(`content`,`
 line-height: 1.25;
 text-overflow: ellipsis;
 overflow: hidden;
 `)])])]),lt=_({name:`InternalSelection`,props:Object.assign(Object.assign({},X.props),{clsPrefix:{type:String,required:!0},bordered:{type:Boolean,default:void 0},active:Boolean,pattern:{type:String,default:``},placeholder:String,selectedOption:{type:Object,default:null},selectedOptions:{type:Array,default:null},labelField:{type:String,default:`label`},valueField:{type:String,default:`value`},multiple:Boolean,filterable:Boolean,clearable:Boolean,disabled:Boolean,size:{type:String,default:`medium`},loading:Boolean,autofocus:Boolean,showArrow:{type:Boolean,default:!0},inputProps:Object,focused:Boolean,renderTag:Function,onKeydown:Function,onClick:Function,onBlur:Function,onFocus:Function,onDeleteOption:Function,maxTagCount:[String,Number],ellipsisTagPopoverProps:Object,onClear:Function,onPatternInput:Function,onPatternFocus:Function,onPatternBlur:Function,renderLabel:Function,status:String,inlineThemeDisabled:Boolean,ignoreComposition:{type:Boolean,default:!0},onResize:Function}),setup(e){let{mergedClsPrefixRef:t,mergedRtlRef:n}=T(e),r=pe(`InternalSelection`,n,t),i=h(null),s=h(null),c=h(null),l=h(null),d=h(null),g=h(null),_=h(null),v=h(null),y=h(null),b=h(null),x=h(!1),S=h(!1),C=h(!1),E=X(`InternalSelection`,`-internal-selection`,ct,Ce,e,f(e,`clsPrefix`)),D=p(()=>e.clearable&&!e.disabled&&(C.value||e.active)),O=p(()=>e.selectedOption?e.renderTag?e.renderTag({option:e.selectedOption,handleClose:()=>{}}):e.renderLabel?e.renderLabel(e.selectedOption,!0):be(e.selectedOption[e.labelField],e.selectedOption,!0):e.placeholder),ee=p(()=>{let t=e.selectedOption;if(t)return t[e.labelField]}),k=p(()=>e.multiple?!!(Array.isArray(e.selectedOptions)&&e.selectedOptions.length):e.selectedOption!==null);function A(){var t;let{value:n}=i;if(n){let{value:r}=s;r&&(r.style.width=`${n.offsetWidth}px`,e.maxTagCount!==`responsive`&&((t=y.value)==null||t.sync({showAllItemsBeforeCalculate:!1})))}}function j(){let{value:e}=b;e&&(e.style.display=`none`)}function M(){let{value:e}=b;e&&(e.style.display=`inline-block`)}o(f(e,`active`),e=>{e||j()}),o(f(e,`pattern`),()=>{e.multiple&&m(A)});function N(t){let{onFocus:n}=e;n&&n(t)}function P(t){let{onBlur:n}=e;n&&n(t)}function F(t){let{onDeleteOption:n}=e;n&&n(t)}function I(t){let{onClear:n}=e;n&&n(t)}function L(t){let{onPatternInput:n}=e;n&&n(t)}function z(e){(!e.relatedTarget||!c.value?.contains(e.relatedTarget))&&N(e)}function te(e){c.value?.contains(e.relatedTarget)||P(e)}function B(e){I(e)}function ne(){C.value=!0}function V(){C.value=!1}function H(t){!e.active||!e.filterable||t.target!==s.value&&t.preventDefault()}function re(e){F(e)}let U=h(!1);function ie(t){if(t.key===`Backspace`&&!U.value&&!e.pattern.length){let{selectedOptions:t}=e;t?.length&&re(t[t.length-1])}}let W=null;function G(t){let{value:n}=i;n&&(n.textContent=t.target.value,A()),e.ignoreComposition&&U.value?W=t:L(t)}function K(){U.value=!0}function oe(){U.value=!1,e.ignoreComposition&&L(W),W=null}function se(t){var n;S.value=!0,(n=e.onPatternFocus)==null||n.call(e,t)}function q(t){var n;S.value=!1,(n=e.onPatternBlur)==null||n.call(e,t)}function J(){var t,n;if(e.filterable)S.value=!1,(t=g.value)==null||t.blur(),(n=s.value)==null||n.blur();else if(e.multiple){let{value:e}=l;e?.blur()}else{let{value:e}=d;e?.blur()}}function Y(){var t,n,r;e.filterable?(S.value=!1,(t=g.value)==null||t.focus()):e.multiple?(n=l.value)==null||n.focus():(r=d.value)==null||r.focus()}function ce(){let{value:e}=s;e&&(M(),e.focus())}function le(){let{value:e}=s;e&&e.blur()}function ue(e){let{value:t}=_;t&&t.setTextContent(`+${e}`)}function de(){let{value:e}=v;return e}function fe(){return s.value}let Z=null;function Q(){Z!==null&&window.clearTimeout(Z)}function me(){e.active||(Q(),Z=window.setTimeout(()=>{k.value&&(x.value=!0)},100))}function he(){Q()}function ge(e){e||(Q(),x.value=!1)}o(k,e=>{e||(x.value=!1)}),a(()=>{u(()=>{let t=g.value;t&&(e.disabled?t.removeAttribute(`tabindex`):t.tabIndex=S.value?-1:0)})}),ze(c,e.onResize);let{inlineThemeDisabled:_e}=e,ve=p(()=>{let{size:t}=e,{common:{cubicBezierEaseInOut:n},self:{fontWeight:r,borderRadius:i,color:a,placeholderColor:o,textColor:s,paddingSingle:c,paddingMultiple:l,caretColor:u,colorDisabled:d,textColorDisabled:f,placeholderColorDisabled:p,colorActive:m,boxShadowFocus:h,boxShadowActive:g,boxShadowHover:_,border:v,borderFocus:y,borderHover:b,borderActive:x,arrowColor:S,arrowColorDisabled:C,loadingColor:w,colorActiveWarning:T,boxShadowFocusWarning:D,boxShadowActiveWarning:O,boxShadowHoverWarning:ee,borderWarning:k,borderFocusWarning:A,borderHoverWarning:j,borderActiveWarning:M,colorActiveError:N,boxShadowFocusError:P,boxShadowActiveError:F,boxShadowHoverError:I,borderError:L,borderFocusError:z,borderHoverError:te,borderActiveError:B,clearColor:ne,clearColorHover:V,clearColorPressed:H,clearSize:re,arrowSize:U,[R(`height`,t)]:ie,[R(`fontSize`,t)]:W}}=E.value,G=ae(c),K=ae(l);return{"--n-bezier":n,"--n-border":v,"--n-border-active":x,"--n-border-focus":y,"--n-border-hover":b,"--n-border-radius":i,"--n-box-shadow-active":g,"--n-box-shadow-focus":h,"--n-box-shadow-hover":_,"--n-caret-color":u,"--n-color":a,"--n-color-active":m,"--n-color-disabled":d,"--n-font-size":W,"--n-height":ie,"--n-padding-single-top":G.top,"--n-padding-multiple-top":K.top,"--n-padding-single-right":G.right,"--n-padding-multiple-right":K.right,"--n-padding-single-left":G.left,"--n-padding-multiple-left":K.left,"--n-padding-single-bottom":G.bottom,"--n-padding-multiple-bottom":K.bottom,"--n-placeholder-color":o,"--n-placeholder-color-disabled":p,"--n-text-color":s,"--n-text-color-disabled":f,"--n-arrow-color":S,"--n-arrow-color-disabled":C,"--n-loading-color":w,"--n-color-active-warning":T,"--n-box-shadow-focus-warning":D,"--n-box-shadow-active-warning":O,"--n-box-shadow-hover-warning":ee,"--n-border-warning":k,"--n-border-focus-warning":A,"--n-border-hover-warning":j,"--n-border-active-warning":M,"--n-color-active-error":N,"--n-box-shadow-focus-error":P,"--n-box-shadow-active-error":F,"--n-box-shadow-hover-error":I,"--n-border-error":L,"--n-border-focus-error":z,"--n-border-hover-error":te,"--n-border-active-error":B,"--n-clear-size":re,"--n-clear-color":ne,"--n-clear-color-hover":V,"--n-clear-color-pressed":H,"--n-arrow-size":U,"--n-font-weight":r}}),ye=_e?w(`internal-selection`,p(()=>e.size[0]),ve,e):void 0;return{mergedTheme:E,mergedClearable:D,mergedClsPrefix:t,rtlEnabled:r,patternInputFocused:S,filterablePlaceholder:O,label:ee,selected:k,showTagsPanel:x,isComposing:U,counterRef:_,counterWrapperRef:v,patternInputMirrorRef:i,patternInputRef:s,selfRef:c,multipleElRef:l,singleElRef:d,patternInputWrapperRef:g,overflowRef:y,inputTagElRef:b,handleMouseDown:H,handleFocusin:z,handleClear:B,handleMouseEnter:ne,handleMouseLeave:V,handleDeleteOption:re,handlePatternKeyDown:ie,handlePatternInputInput:G,handlePatternInputBlur:q,handlePatternInputFocus:se,handleMouseEnterCounter:me,handleMouseLeaveCounter:he,handleFocusout:te,handleCompositionEnd:oe,handleCompositionStart:K,onPopoverUpdateShow:ge,focus:Y,focusInput:ce,blur:J,blurInput:le,updateCounter:ue,getCounter:de,getTail:fe,renderLabel:e.renderLabel,cssVars:_e?void 0:ve,themeClass:ye?.themeClass,onRender:ye?.onRender}},render(){let{status:e,multiple:t,size:r,disabled:i,filterable:a,maxTagCount:o,bordered:s,clsPrefix:c,ellipsisTagPopoverProps:l,onRender:u,renderTag:d,renderLabel:f}=this;u?.();let p=o===`responsive`,m=typeof o==`number`,h=p||m,_=n(M,null,{default:()=>n(st,{clsPrefix:c,loading:this.loading,showArrow:this.showArrow,showClear:this.mergedClearable&&this.selected,onClear:this.handleClear},{default:()=>{var e;return(e=this.$slots).arrow?.call(e)}})}),v;if(t){let{labelField:e}=this,t=t=>n(`div`,{class:`${c}-base-selection-tag-wrapper`,key:t.value},d?d({option:t,handleClose:()=>{this.handleDeleteOption(t)}}):n(ot,{size:r,closable:!t.disabled,disabled:i,onClose:()=>{this.handleDeleteOption(t)},internalCloseIsButtonTag:!1,internalCloseFocusable:!1},{default:()=>f?f(t,!0):be(t[e],t,!0)})),s=()=>(m?this.selectedOptions.slice(0,o):this.selectedOptions).map(t),u=a?n(`div`,{class:`${c}-base-selection-input-tag`,ref:`inputTagElRef`,key:`__input-tag__`},n(`input`,Object.assign({},this.inputProps,{ref:`patternInputRef`,tabindex:-1,disabled:i,value:this.pattern,autofocus:this.autofocus,class:`${c}-base-selection-input-tag__input`,onBlur:this.handlePatternInputBlur,onFocus:this.handlePatternInputFocus,onKeydown:this.handlePatternKeyDown,onInput:this.handlePatternInputInput,onCompositionstart:this.handleCompositionStart,onCompositionend:this.handleCompositionEnd})),n(`span`,{ref:`patternInputMirrorRef`,class:`${c}-base-selection-input-tag__mirror`},this.pattern)):null,y=p?()=>n(`div`,{class:`${c}-base-selection-tag-wrapper`,ref:`counterWrapperRef`},n(ot,{size:r,ref:`counterRef`,onMouseenter:this.handleMouseEnterCounter,onMouseleave:this.handleMouseLeaveCounter,disabled:i})):void 0,b;if(m){let e=this.selectedOptions.length-o;e>0&&(b=n(`div`,{class:`${c}-base-selection-tag-wrapper`,key:`__counter__`},n(ot,{size:r,ref:`counterRef`,onMouseenter:this.handleMouseEnterCounter,disabled:i},{default:()=>`+${e}`})))}let x=p?a?n(Re,{ref:`overflowRef`,updateCounter:this.updateCounter,getCounter:this.getCounter,getTail:this.getTail,style:{width:`100%`,display:`flex`,overflow:`hidden`}},{default:s,counter:y,tail:()=>u}):n(Re,{ref:`overflowRef`,updateCounter:this.updateCounter,getCounter:this.getCounter,style:{width:`100%`,display:`flex`,overflow:`hidden`}},{default:s,counter:y}):m&&b?s().concat(b):s(),S=h?()=>n(`div`,{class:`${c}-base-selection-popover`},p?s():this.selectedOptions.map(t)):void 0,C=h?Object.assign({show:this.showTagsPanel,trigger:`hover`,overlap:!0,placement:`top`,width:`trigger`,onUpdateShow:this.onPopoverUpdateShow,theme:this.mergedTheme.peers.Popover,themeOverrides:this.mergedTheme.peerOverrides.Popover},l):null,w=!this.selected&&(!this.active||!this.pattern&&!this.isComposing)?n(`div`,{class:`${c}-base-selection-placeholder ${c}-base-selection-overlay`},n(`div`,{class:`${c}-base-selection-placeholder__inner`},this.placeholder)):null,T=a?n(`div`,{ref:`patternInputWrapperRef`,class:`${c}-base-selection-tags`},x,p?null:u,_):n(`div`,{ref:`multipleElRef`,class:`${c}-base-selection-tags`,tabindex:i?void 0:0},x,_);v=n(g,null,h?n(Y,Object.assign({},C,{scrollable:!0,style:`max-height: calc(var(--v-target-height) * 6.6);`}),{trigger:()=>T,default:S}):T,w)}else if(a){let e=this.pattern||this.isComposing,t=this.active?!e:!this.selected,r=!this.active&&this.selected;v=n(`div`,{ref:`patternInputWrapperRef`,class:`${c}-base-selection-label`,title:this.patternInputFocused?void 0:Be(this.label)},n(`input`,Object.assign({},this.inputProps,{ref:`patternInputRef`,class:`${c}-base-selection-input`,value:this.active?this.pattern:``,placeholder:``,readonly:i,disabled:i,tabindex:-1,autofocus:this.autofocus,onFocus:this.handlePatternInputFocus,onBlur:this.handlePatternInputBlur,onInput:this.handlePatternInputInput,onCompositionstart:this.handleCompositionStart,onCompositionend:this.handleCompositionEnd})),r?n(`div`,{class:`${c}-base-selection-label__render-label ${c}-base-selection-overlay`,key:`input`},n(`div`,{class:`${c}-base-selection-overlay__wrapper`},d?d({option:this.selectedOption,handleClose:()=>{}}):f?f(this.selectedOption,!0):be(this.label,this.selectedOption,!0))):null,t?n(`div`,{class:`${c}-base-selection-placeholder ${c}-base-selection-overlay`,key:`placeholder`},n(`div`,{class:`${c}-base-selection-overlay__wrapper`},this.filterablePlaceholder)):null,_)}else v=n(`div`,{ref:`singleElRef`,class:`${c}-base-selection-label`,tabindex:this.disabled?void 0:0},this.label===void 0?n(`div`,{class:`${c}-base-selection-placeholder ${c}-base-selection-overlay`,key:`placeholder`},n(`div`,{class:`${c}-base-selection-placeholder__inner`},this.placeholder)):n(`div`,{class:`${c}-base-selection-input`,title:Be(this.label),key:`input`},n(`div`,{class:`${c}-base-selection-input__content`},d?d({option:this.selectedOption,handleClose:()=>{}}):f?f(this.selectedOption,!0):be(this.label,this.selectedOption,!0))),_);return n(`div`,{ref:`selfRef`,class:[`${c}-base-selection`,this.rtlEnabled&&`${c}-base-selection--rtl`,this.themeClass,e&&`${c}-base-selection--${e}-status`,{[`${c}-base-selection--active`]:this.active,[`${c}-base-selection--selected`]:this.selected||this.active&&this.pattern,[`${c}-base-selection--disabled`]:this.disabled,[`${c}-base-selection--multiple`]:this.multiple,[`${c}-base-selection--focus`]:this.focused}],style:this.cssVars,onClick:this.onClick,onMouseenter:this.handleMouseEnter,onMouseleave:this.handleMouseLeave,onKeydown:this.onKeydown,onFocusin:this.handleFocusin,onFocusout:this.handleFocusout,onMousedown:this.handleMouseDown},v,s?n(`div`,{class:`${c}-base-selection__border`}):null,s?n(`div`,{class:`${c}-base-selection__state-border`}):null)}});function ut(e){return e.type===`group`}function dt(e){return e.type===`ignored`}function ft(e,t){try{return!!(1+t.toString().toLowerCase().indexOf(e.trim().toLowerCase()))}catch{return!1}}function pt(e,t){return{getIsGroup:ut,getIgnored:dt,getKey(t){return ut(t)?t.name||t.key||`key-required`:t[e]},getChildren(e){return e[t]}}}function mt(e,t,n,r){if(!t)return e;function i(e){if(!Array.isArray(e))return[];let a=[];for(let o of e)if(ut(o)){let e=i(o[r]);e.length&&a.push(Object.assign({},o,{[r]:e}))}else if(dt(o))continue;else t(n,o)&&a.push(o);return a}return i(e)}function ht(e,t,n){let r=new Map;return e.forEach(e=>{ut(e)?e[n].forEach(e=>{r.set(e[t],e)}):r.set(e[t],e)}),r}var gt=E([D(`select`,`
 z-index: auto;
 outline: none;
 width: 100%;
 position: relative;
 font-weight: var(--n-font-weight);
 `),D(`select-menu`,`
 margin: 4px 0;
 box-shadow: var(--n-menu-box-shadow);
 `,[H({originalTransition:`background-color .3s var(--n-bezier), box-shadow .3s var(--n-bezier)`})])]),_t=_({name:`Select`,props:Object.assign(Object.assign({},X.props),{to:re.propTo,bordered:{type:Boolean,default:void 0},clearable:Boolean,clearCreatedOptionsOnClear:{type:Boolean,default:!0},clearFilterAfterSelect:{type:Boolean,default:!0},options:{type:Array,default:()=>[]},defaultValue:{type:[String,Number,Array],default:null},keyboard:{type:Boolean,default:!0},value:[String,Number,Array],placeholder:String,menuProps:Object,multiple:Boolean,size:String,menuSize:{type:String},filterable:Boolean,disabled:{type:Boolean,default:void 0},remote:Boolean,loading:Boolean,filter:Function,placement:{type:String,default:`bottom-start`},widthMode:{type:String,default:`trigger`},tag:Boolean,onCreate:Function,fallbackOption:{type:[Function,Boolean],default:void 0},show:{type:Boolean,default:void 0},showArrow:{type:Boolean,default:!0},maxTagCount:[Number,String],ellipsisTagPopoverProps:Object,consistentMenuWidth:{type:Boolean,default:!0},virtualScroll:{type:Boolean,default:!0},labelField:{type:String,default:`label`},valueField:{type:String,default:`value`},childrenField:{type:String,default:`children`},renderLabel:Function,renderOption:Function,renderTag:Function,"onUpdate:value":[Function,Array],inputProps:Object,nodeProps:Function,ignoreComposition:{type:Boolean,default:!0},showOnFocus:Boolean,onUpdateValue:[Function,Array],onBlur:[Function,Array],onClear:[Function,Array],onFocus:[Function,Array],onScroll:[Function,Array],onSearch:[Function,Array],onUpdateShow:[Function,Array],"onUpdate:show":[Function,Array],displayDirective:{type:String,default:`show`},resetMenuOnOptionsChange:{type:Boolean,default:!0},status:String,showCheckmark:{type:Boolean,default:!0},scrollbarProps:Object,onChange:[Function,Array],items:Array}),slots:Object,setup(e){let{mergedClsPrefixRef:t,mergedBorderedRef:n,namespaceRef:r,inlineThemeDisabled:i,mergedComponentPropsRef:a}=T(e),s=X(`Select`,`-select`,gt,Se,e,t),c=h(e.defaultValue),l=fe(f(e,`value`),c),u=h(!1),d=h(``),m=ie(e,[`items`,`options`]),g=h([]),_=h([]),v=p(()=>_.value.concat(g.value).concat(m.value)),y=p(()=>{let{filter:t}=e;if(t)return t;let{labelField:n,valueField:r}=e;return(e,t)=>{if(!t)return!1;let i=t[n];if(typeof i==`string`)return ft(e,i);let a=t[r];return typeof a==`string`?ft(e,a):typeof a==`number`&&ft(e,String(a))}}),b=p(()=>{if(e.remote)return m.value;{let{value:t}=v,{value:n}=d;return!n.length||!e.filterable?t:mt(t,y.value,n,e.childrenField)}}),x=p(()=>{let{valueField:t,childrenField:n}=e,r=pt(t,n);return _e(b.value,r)}),S=p(()=>ht(v.value,e.valueField,e.childrenField)),C=h(!1),E=fe(f(e,`show`),C),D=h(null),O=h(null),A=h(null),{localeRef:j}=me(`Select`),M=p(()=>e.placeholder??j.value.placeholder),N=[],P=h(new Map),F=p(()=>{let{fallbackOption:t}=e;if(t===void 0){let{labelField:t,valueField:n}=e;return e=>({[t]:String(e),[n]:e})}return t===!1?!1:e=>Object.assign(t(e),{value:e})});function I(t){let n=e.remote,{value:r}=P,{value:i}=S,{value:a}=F,o=[];return t.forEach(e=>{if(i.has(e))o.push(i.get(e));else if(n&&r.has(e))o.push(r.get(e));else if(a){let t=a(e);t&&o.push(t)}}),o}let L=p(()=>{if(e.multiple){let{value:e}=l;return Array.isArray(e)?I(e):[]}return null}),R=p(()=>{let{value:t}=l;return!e.multiple&&!Array.isArray(t)?t===null?null:I([t])[0]||null:null}),z=k(e,{mergedSize:t=>{let{size:n}=e;if(n)return n;let{mergedSize:r}=t||{};return r?.value?r.value:a?.value?.Select?.size||`medium`}}),{mergedSizeRef:te,mergedDisabledRef:B,mergedStatusRef:V}=z;function H(t,n){let{onChange:r,"onUpdate:value":i,onUpdateValue:a}=e,{nTriggerFormChange:o,nTriggerFormInput:s}=z;r&&J(r,t,n),a&&J(a,t,n),i&&J(i,t,n),c.value=t,o(),s()}function U(t){let{onBlur:n}=e,{nTriggerFormBlur:r}=z;n&&J(n,t),r()}function W(){let{onClear:t}=e;t&&J(t)}function G(t){let{onFocus:n,showOnFocus:r}=e,{nTriggerFormFocus:i}=z;n&&J(n,t),i(),r&&q()}function ae(t){let{onSearch:n}=e;n&&J(n,t)}function K(t){let{onScroll:n}=e;n&&J(n,t)}function oe(){var t;let{remote:n,multiple:r}=e;if(n){let{value:n}=P;if(r){let{valueField:r}=e;(t=L.value)==null||t.forEach(e=>{n.set(e[r],e)})}else{let t=R.value;t&&n.set(t[e.valueField],t)}}}function se(t){let{onUpdateShow:n,"onUpdate:show":r}=e;n&&J(n,t),r&&J(r,t),C.value=t}function q(){B.value||(se(!0),C.value=!0,e.filterable&&Ne())}function Y(){se(!1)}function ce(){d.value=``,_.value=N}let le=h(!1);function ue(){e.filterable&&(le.value=!0)}function de(){e.filterable&&(le.value=!1,E.value||ce())}function pe(){B.value||(E.value?e.filterable?Ne():Y():q())}function Z(e){(A.value?.selfRef)?.contains(e.relatedTarget)||(u.value=!1,U(e),Y())}function Q(e){G(e),u.value=!0}function he(){u.value=!0}function ve(e){D.value?.$el.contains(e.relatedTarget)||(u.value=!1,U(e),Y())}function be(){var e;(e=D.value)==null||e.focus(),Y()}function xe(e){E.value&&(D.value?.$el.contains(ee(e))||Y())}function Ce(t){if(!Array.isArray(t))return[];if(F.value)return Array.from(t);{let{remote:n}=e,{value:r}=S;if(n){let{value:e}=P;return t.filter(t=>r.has(t)||e.has(t))}else return t.filter(e=>r.has(e))}}function we(e){Te(e.rawNode)}function Te(t){if(B.value)return;let{tag:n,remote:r,clearFilterAfterSelect:i,valueField:a}=e;if(n&&!r){let{value:e}=_,t=e[0]||null;if(t){let e=g.value;e.length?e.push(t):g.value=[t],_.value=N}}if(r&&P.value.set(t[a],t),e.multiple){let e=Ce(l.value),o=e.findIndex(e=>e===t[a]);if(~o){if(e.splice(o,1),n&&!r){let e=Ee(t[a]);~e&&(g.value.splice(e,1),i&&(d.value=``))}}else e.push(t[a]),i&&(d.value=``);H(e,I(e))}else{if(n&&!r){let e=Ee(t[a]);~e?g.value=[g.value[e]]:g.value=N}Me(),Y(),H(t[a],t)}}function Ee(t){return g.value.findIndex(n=>n[e.valueField]===t)}function De(t){E.value||q();let{value:n}=t.target;d.value=n;let{tag:r,remote:i}=e;if(ae(n),r&&!i){if(!n){_.value=N;return}let{onCreate:t}=e,r=t?t(n):{[e.labelField]:n,[e.valueField]:n},{valueField:i,labelField:a}=e;m.value.some(e=>e[i]===r[i]||e[a]===r[a])||g.value.some(e=>e[i]===r[i]||e[a]===r[a])?_.value=N:_.value=[r]}}function Oe(t){t.stopPropagation();let{multiple:n,tag:r,remote:i,clearCreatedOptionsOnClear:a}=e;!n&&e.filterable&&Y(),r&&!i&&a&&(g.value=N),W(),n?H([],[]):H(null,null)}function ke(e){!ge(e,`action`)&&!ge(e,`empty`)&&!ge(e,`header`)&&e.preventDefault()}function Ae(e){K(e)}function je(t){var n,r,i;if(!e.keyboard){t.preventDefault();return}switch(t.key){case` `:if(e.filterable)break;t.preventDefault();case`Enter`:if(!D.value?.isComposing){if(E.value){let t=A.value?.getPendingTmNode();t?we(t):e.filterable||(Y(),Me())}else if(q(),e.tag&&le.value){let t=_.value[0];if(t){let n=t[e.valueField],{value:r}=l;e.multiple&&Array.isArray(r)&&r.includes(n)||Te(t)}}}t.preventDefault();break;case`ArrowUp`:if(t.preventDefault(),e.loading)return;E.value&&((n=A.value)==null||n.prev());break;case`ArrowDown`:if(t.preventDefault(),e.loading)return;E.value?(r=A.value)==null||r.next():q();break;case`Escape`:E.value&&(ye(t),Y()),(i=D.value)==null||i.focus();break}}function Me(){var e;(e=D.value)==null||e.focus()}function Ne(){var e;(e=D.value)==null||e.focusInput()}function Pe(){var e;E.value&&((e=O.value)==null||e.syncPosition())}oe(),o(f(e,`options`),oe);let Fe={focus:()=>{var e;(e=D.value)==null||e.focus()},focusInput:()=>{var e;(e=D.value)==null||e.focusInput()},blur:()=>{var e;(e=D.value)==null||e.blur()},blurInput:()=>{var e;(e=D.value)==null||e.blurInput()}},Ie=p(()=>{let{self:{menuBoxShadow:e}}=s.value;return{"--n-menu-box-shadow":e}}),$=i?w(`select`,void 0,Ie,e):void 0;return Object.assign(Object.assign({},Fe),{mergedStatus:V,mergedClsPrefix:t,mergedBordered:n,namespace:r,treeMate:x,isMounted:ne(),triggerRef:D,menuRef:A,pattern:d,uncontrolledShow:C,mergedShow:E,adjustedTo:re(e),uncontrolledValue:c,mergedValue:l,followerRef:O,localizedPlaceholder:M,selectedOption:R,selectedOptions:L,mergedSize:te,mergedDisabled:B,focused:u,activeWithoutMenuOpen:le,inlineThemeDisabled:i,onTriggerInputFocus:ue,onTriggerInputBlur:de,handleTriggerOrMenuResize:Pe,handleMenuFocus:he,handleMenuBlur:ve,handleMenuTabOut:be,handleTriggerClick:pe,handleToggle:we,handleDeleteOption:Te,handlePatternInput:De,handleClear:Oe,handleTriggerBlur:Z,handleTriggerFocus:Q,handleKeydown:je,handleMenuAfterLeave:ce,handleMenuClickOutside:xe,handleMenuScroll:Ae,handleMenuKeydown:je,handleMenuMousedown:ke,mergedTheme:s,cssVars:i?void 0:Ie,themeClass:$?.themeClass,onRender:$?.onRender})},render(){return n(`div`,{class:`${this.mergedClsPrefix}-select`},n(le,null,{default:()=>[n(q,null,{default:()=>n(lt,{ref:`triggerRef`,inlineThemeDisabled:this.inlineThemeDisabled,status:this.mergedStatus,inputProps:this.inputProps,clsPrefix:this.mergedClsPrefix,showArrow:this.showArrow,maxTagCount:this.maxTagCount,ellipsisTagPopoverProps:this.ellipsisTagPopoverProps,bordered:this.mergedBordered,active:this.activeWithoutMenuOpen||this.mergedShow,pattern:this.pattern,placeholder:this.localizedPlaceholder,selectedOption:this.selectedOption,selectedOptions:this.selectedOptions,multiple:this.multiple,renderTag:this.renderTag,renderLabel:this.renderLabel,filterable:this.filterable,clearable:this.clearable,disabled:this.mergedDisabled,size:this.mergedSize,theme:this.mergedTheme.peers.InternalSelection,labelField:this.labelField,valueField:this.valueField,themeOverrides:this.mergedTheme.peerOverrides.InternalSelection,loading:this.loading,focused:this.focused,onClick:this.handleTriggerClick,onDeleteOption:this.handleDeleteOption,onPatternInput:this.handlePatternInput,onClear:this.handleClear,onBlur:this.handleTriggerBlur,onFocus:this.handleTriggerFocus,onKeydown:this.handleKeydown,onPatternBlur:this.onTriggerInputBlur,onPatternFocus:this.onTriggerInputFocus,onResize:this.handleTriggerOrMenuResize,ignoreComposition:this.ignoreComposition},{arrow:()=>{var e;return[(e=this.$slots).arrow?.call(e)]}})}),n(x,{ref:`followerRef`,show:this.mergedShow,to:this.adjustedTo,teleportDisabled:this.adjustedTo===re.tdkey,containerClass:this.namespace,width:this.consistentMenuWidth?`target`:void 0,minWidth:`target`,placement:this.placement},{default:()=>n(v,{name:`fade-in-scale-up-transition`,appear:this.isMounted,onAfterLeave:this.handleMenuAfterLeave},{default:()=>{var e;return this.mergedShow||this.displayDirective===`show`?((e=this.onRender)==null||e.call(this),d(n(tt,Object.assign({},this.menuProps,{ref:`menuRef`,onResize:this.handleTriggerOrMenuResize,inlineThemeDisabled:this.inlineThemeDisabled,virtualScroll:this.consistentMenuWidth&&this.virtualScroll,class:[`${this.mergedClsPrefix}-select-menu`,this.themeClass,this.menuProps?.class],clsPrefix:this.mergedClsPrefix,focusable:!0,labelField:this.labelField,valueField:this.valueField,autoPending:!0,nodeProps:this.nodeProps,theme:this.mergedTheme.peers.InternalSelectMenu,themeOverrides:this.mergedTheme.peerOverrides.InternalSelectMenu,treeMate:this.treeMate,multiple:this.multiple,size:this.menuSize,renderOption:this.renderOption,renderLabel:this.renderLabel,value:this.mergedValue,style:[this.menuProps?.style,this.cssVars],onToggle:this.handleToggle,onScroll:this.handleMenuScroll,onFocus:this.handleMenuFocus,onBlur:this.handleMenuBlur,onKeydown:this.handleMenuKeydown,onTabOut:this.handleMenuTabOut,onMousedown:this.handleMenuMousedown,show:this.mergedShow,showCheckmark:this.showCheckmark,resetMenuOnOptionsChange:this.resetMenuOnOptionsChange,scrollbarProps:this.scrollbarProps}),{empty:()=>{var e;return[(e=this.$slots).empty?.call(e)]},header:()=>{var e;return[(e=this.$slots).header?.call(e)]},action:()=>{var e;return[(e=this.$slots).action?.call(e)]}}),this.displayDirective===`show`?[[y,this.mergedShow],[V,this.handleMenuClickOutside,void 0,{capture:!0}]]:[[V,this.handleMenuClickOutside,void 0,{capture:!0}]])):null}})})]}))}});export{qe as a,Je as i,st as n,Ie as o,ot as r,_t as t};