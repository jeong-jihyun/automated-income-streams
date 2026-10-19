// 등록 화면 오른쪽 아래에 복사 버튼만 보여 준다. 페이지 입력칸을 건드리지 않는다.
(function () {
  chrome.storage.local.get('listing', ({ listing }) => {
    if (!listing) return
    const L = ListingLib.parseListing(listing)
    const box = document.createElement('div')
    box.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:2147483647;background:#fff;border:2px solid #1F3864;border-radius:8px;padding:8px;font:13px sans-serif;box-shadow:0 2px 8px #0003'
    box.append(Object.assign(document.createElement('b'), { textContent: '등록 도우미 (복사만)' }))
    ;[['제목 복사', L.title], ['설명 복사', L.description], ['태그 복사', ListingLib.tagLine(L)]].forEach(([name, text]) => {
      const b = document.createElement('button')
      b.textContent = name; b.style.cssText = 'display:block;margin-top:6px;width:100%'
      b.onclick = async () => { await navigator.clipboard.writeText(text); b.textContent = name + ' ✓' }
      box.append(b)
    })
    document.body.append(box)
  })
})()
