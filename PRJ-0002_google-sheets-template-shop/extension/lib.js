// 상품 문구 JSON(engine이 만든 listing_*.json)을 읽고 검사한다. 브라우저·Node 모두에서 동작.
(function (root) {
  function parseListing(text) {
    let o
    try { o = JSON.parse(text) } catch (e) { throw new Error('JSON 형식이 올바르지 않습니다') }
    if (!o || typeof o.title !== 'string' || !o.title.trim()) throw new Error('title이 없습니다')
    if (typeof o.description !== 'string') throw new Error('description이 없습니다')
    if (!Array.isArray(o.tags)) throw new Error('tags가 배열이 아닙니다')
    return { title: o.title.trim(), description: o.description, tags: o.tags.map(String) }
  }
  function tagLine(listing) { return listing.tags.join(', ') }
  const api = { parseListing, tagLine }
  if (typeof module !== 'undefined' && module.exports) module.exports = api
  else root.ListingLib = api
})(typeof self !== 'undefined' ? self : this)
