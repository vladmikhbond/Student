let defense = { "Focus": true, "Moving": 0, "Blind": 100 }; 

if (defense.Focus) {
   window.addEventListener('focus', () => { 
      focusCounter.value++; 
      console.log(focusCounter.value)
   })
}


if (defense.Moving > 0) {
   let moving = 0;
   document.addEventListener('mousemove', () => {
      moving = 1;
   });

   setInterval(() => {
      if (!moving) {
         focusCounter.value++;
         alert('You are not active');
      }
      moving = 0;
   }, defense.Moving * 1000);

}


if (defense.Blind > 0) {
   const fillColor = 'rgba(224, 224, 224, 0.99)';
   const absCont = document.getElementById('absCont');
   const canvas = document.getElementById('canvas2');
   const questionText = document.getElementById('questionText');
   absCont.style.position = 'relative';
   canvas.style.display = 'block';
   const ctx = canvas.getContext("2d");
 
   let rect;
   setTimeout(resizeAndClearCanvas, 0);

   function resizeAndClearCanvas() {
      rect = questionText.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      ctx.fillStyle = fillColor;
      ctx.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight);
   }

   window.addEventListener('resize', resizeAndClearCanvas);
 
   canvas.addEventListener('mouseleave', resizeAndClearCanvas);

   canvas.addEventListener('mousemove', (event) => {
      resizeAndClearCanvas();

      const x = event.clientX - rect.left; 
      const y = event.clientY - rect.top;
      let R = rect.height / 2;
      if (R < defense.Blind) {
         R = defense.Blind;
      }
      ctx.save()
      ctx.globalCompositeOperation = 'destination-out';
      ctx.beginPath();
      ctx.arc(x, y, R, 0, 2 * Math.PI);
      ctx.fill();
      ctx.restore()
   });

}
