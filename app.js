
const $ = (s, p=document) => p.querySelector(s);
const toast = (message) => {
  const el = $("#toast"); el.textContent = message; el.classList.add("show");
  clearTimeout(window.__toastTimer); window.__toastTimer = setTimeout(()=>el.classList.remove("show"),2300);
};
const today = new Intl.DateTimeFormat("ru-RU",{day:"numeric",month:"long",year:"numeric"}).format(new Date());
$("#today").textContent = today;
$("#menuBtn").addEventListener("click",()=>$("#sidebar").classList.toggle("open"));
document.querySelectorAll(".nav-link").forEach(link=>link.addEventListener("click",()=>{
  document.querySelectorAll(".nav-link").forEach(x=>x.classList.remove("active"));
  link.classList.add("active");
  $("#currentSection").textContent=link.textContent.trim();
  $("#sidebar").classList.remove("open");
}));
$("#themeBtn").addEventListener("click",()=>{document.body.classList.toggle("light");toast(document.body.classList.contains("light")?"Светлая тема включена":"Тёмная тема включена")});
$("#compactToggle").addEventListener("change",e=>document.body.classList.toggle("compact",e.target.checked));
$("#noticeToggle").addEventListener("change",e=>{$(".notice").classList.toggle("hidden",!e.target.checked)});
$(".notice-close").addEventListener("click",()=>{$(".notice").classList.add("hidden");$("#noticeToggle").checked=false});
$("#helpBtn").addEventListener("click",()=>toast("XNet v0.1 — стартовая панель проекта."));
const search=$("#globalSearch");
search.addEventListener("input",()=>{
  const q=search.value.toLowerCase().trim();
  document.querySelectorAll(".service-card,.doc-card,.road-item,.nav-link").forEach(el=>{
    el.classList.toggle("hidden",!!q&&!el.textContent.toLowerCase().includes(q));
  });
});
document.addEventListener("keydown",e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();search.focus()}
  if(e.key==="Escape"){search.value="";search.dispatchEvent(new Event("input"));search.blur();$("#sidebar").classList.remove("open")}
});
