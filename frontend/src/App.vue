<template>
  <div class="page">
    <header class="hero">
      <p class="eyebrow">DIPLOMSKI RAD</p>
      <h1>Segmentacija MRI snimki mozga</h1>
      <p class="lede">
        Učitaj MRI snimku mozga i prikaži automatsku segmentaciju tumorskih promjena.
      </p>
    </header>

    <section class="content">
      <PredictForm />
    </section>
  </div>
</template>

<script setup>
import PredictForm from './components/PredictForm.vue'
</script>

<style>
:root {
  color-scheme: dark;
  --bg: radial-gradient(circle at 20% 20%, rgba(118, 74, 255, 0.15) 0, transparent 25%),
        radial-gradient(circle at 80% 0%, rgba(41, 196, 255, 0.12) 0, transparent 30%),
        #050915;
  --panel: rgba(255, 255, 255, 0.04);
  --border: rgba(255, 255, 255, 0.08);
  --text: #e9edf5;
  --muted: #c6cee4;
  --accent: linear-gradient(135deg, #8a2be2, #1e90ff);
}

* {
  box-sizing: border-box;
}

body, html, #app {
  margin: 0;
  min-height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
}

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px 60px;
}

.hero {
  text-align: center;
  margin-bottom: 32px;
  padding: 28px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
  position: relative;
  overflow: hidden;
}

.eyebrow {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(99, 140, 255, 0.12);
  color: #9eb8ff;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 12px;
  margin-bottom: 12px;
}

h1 {
  margin: 0 0 12px;
  font-size: 40px;
  background: linear-gradient(120deg, #ffffff, #93c5fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.lede {
  margin: 0 auto;
  max-width: 720px;
  color: #c6cee4;
  line-height: 1.6;
}

.content {
  display: grid;
  gap: 20px;
}
</style>
