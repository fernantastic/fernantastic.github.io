(function () {
  var cv = document.querySelector('.cv-content');
  if (!cv) return;

  var A4_RATIO = 297 / 210;

  function paginate() {
    if (cv.classList.contains('cv-paginated')) return;
    if (cv.children.length === 0) return;

    var widthPx = cv.clientWidth;
    if (widthPx < 400) return; // skip on narrow / mobile
    var pxPerMm = widthPx / 210;
    var pageHeightPx = Math.round(297 * pxPerMm);
    var style = getComputedStyle(cv);
    var padTop = parseFloat(style.paddingTop);
    var padBottom = parseFloat(style.paddingBottom);
    var contentPerPage = pageHeightPx - padTop - padBottom;

    var children = Array.from(cv.children);
    var heights = children.map(function (c) { return c.getBoundingClientRect().height; });

    var pages = [];
    var group = [];
    var acc = 0;

    for (var i = 0; i < children.length; i++) {
      var h = heights[i];
      if (acc + h > contentPerPage && group.length > 0) {
        pages.push(group);
        group = [];
        acc = 0;
      }
      group.push(children[i]);
      acc += h;
    }
    if (group.length > 0) pages.push(group);
    if (pages.length <= 1) return;

    cv.innerHTML = '';
    cv.classList.add('cv-paginated');
    for (var p = 0; p < pages.length; p++) {
      var pageDiv = document.createElement('div');
      pageDiv.className = 'cv-page';
      for (var c = 0; c < pages[p].length; c++) {
        pageDiv.appendChild(pages[p][c]);
      }
      cv.appendChild(pageDiv);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', paginate);
  } else {
    paginate();
  }
})();
