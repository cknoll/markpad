console.log('[script main.js] loaded: ' + Date());

const btn = document.getElementById('button');
btn.addEventListener('click', function() {
    console.log('button clicked ' + Date());
});

btn.addEventListener('click', function() {
    alert("JavaScript works :)");
});
