<script>
(function () {
  var ua = navigator.userAgent || '';
  var fb = document.getElementById('static-fallback');
  if (fb) { fb.style.display = 'none'; }
  if (/MicroMessenger/i.test(ua) && !document.getElementById('wxbar')) {
    document.body.classList.add('wx');
    var bar = document.createElement('div');
    bar.id = 'wxbar';
    bar.innerHTML = '如页面显示不完整，请点右上角 <b>···</b> → 选择 <b>「在浏览器打开」</b>';
    document.body.appendChild(bar);
  }
})();
</script>
