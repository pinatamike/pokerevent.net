/* PokerEvent bilingual routing: include on every EN and ES page once translations are published. */
(function(){
  'use strict';
  var key='pokerevent-language';
  var spanishCountries=new Set(['AR','BO','BR','CL','CO','CR','CU','DO','EC','SV','GT','HN','MX','NI','PA','PY','PE','PR','UY','VE','ES']);
  var path=location.pathname;
  var isSpanish=path==='/es'||path.startsWith('/es/');
  var enPath=isSpanish?(path.replace(/^\/es(?=\/|$)/,'')||'/'):path;
  var esPath='/es'+(enPath==='/'?'/':enPath);
  function go(lang){var target=lang==='es'?esPath:enPath;if(target!==path)location.replace(target);}
  function switchTo(lang){try{localStorage.setItem(key,lang);}catch(e){}go(lang);}
  var selected=null;try{selected=localStorage.getItem(key);}catch(e){}
  function makeToggle(){
    var header=document.querySelector('header');if(!header)return;
    var div=document.createElement('div');div.className='pe-language';div.setAttribute('aria-label','Website language');
    div.innerHTML='<button type="button" data-lang="en" aria-label="English">EN</button><span aria-hidden="true">|</span><button type="button" data-lang="es" aria-label="Español">ES</button>';
    div.querySelectorAll('button').forEach(function(b){var lang=b.dataset.lang;b.setAttribute('aria-pressed',String((isSpanish?'es':'en')===lang));b.addEventListener('click',function(){switchTo(lang);});});
    header.appendChild(div);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',makeToggle);else makeToggle();
  if(selected==='en'||selected==='es'){go(selected);return;}
  // The geolocation endpoint returns a country code without requiring an API key.
  // Fail open: retain the requested page if geolocation is unavailable.
  fetch('https://ipapi.co/country/',{signal:AbortSignal.timeout(2500)}).then(function(r){if(!r.ok)throw Error('geo');return r.text();}).then(function(country){
    var lang=spanishCountries.has(country.trim().toUpperCase())?'es':'en';go(lang);
  }).catch(function(){
    var locale=(navigator.language||'').toLowerCase();
    if(locale.startsWith('es')||locale.startsWith('pt-br'))go('es');
  });
})();
