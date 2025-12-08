export async function fetchHealth(){
  const res = await fetch('/health');
  if(!res.ok){ throw new Error('Network response was not ok'); }
  return res.json();
}

export async function fetchConfig(){
  const res = await fetch('/config');
  if(!res.ok){ throw new Error('Network response was not ok'); }
  return res.json();
}
