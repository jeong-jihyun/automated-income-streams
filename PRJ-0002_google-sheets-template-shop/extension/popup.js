const t = document.getElementById('t'), msg = document.getElementById('msg')
chrome.storage.local.get('listing', ({ listing }) => { if (listing) t.value = listing })
document.getElementById('save').onclick = () => {
  try { ListingLib.parseListing(t.value); chrome.storage.local.set({ listing: t.value }); msg.textContent = '저장됨 ✓' }
  catch (e) { msg.textContent = e.message }
}
