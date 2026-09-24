/* Chart.js ustida yupqa qatlam: ranglar CSS tokenlardan olinadi, tema almashganda qayta chiziladi. */
(function () {
  'use strict';
  const charts = [];

  function css(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  const money = n => IDGPS.formatMoney(n) + " so'm";
  const compact = n => {
    const abs = Math.abs(n);
    if (abs >= 1e9) return (n / 1e9).toFixed(1).replace('.0', '') + ' mlrd';
    if (abs >= 1e6) return (n / 1e6).toFixed(1).replace('.0', '') + ' mln';
    if (abs >= 1e3) return Math.round(n / 1e3) + ' ming';
    return String(n);
  };

  function baseOptions(opts) {
    const text2 = css('--text-2');
    const muted = css('--muted');
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      animation: { duration: 500 },
      plugins: {
        legend: {
          display: opts.legend !== false,
          position: 'top', align: 'end',
          labels: { color: text2, boxWidth: 10, boxHeight: 10, useBorderRadius: true, borderRadius: 3, font: { family: 'Inter', size: 12, weight: '500' } },
        },
        tooltip: {
          backgroundColor: css('--surface'), titleColor: css('--text'), bodyColor: text2,
          borderColor: css('--border'), borderWidth: 1, padding: 12, cornerRadius: 10, boxPadding: 4,
          usePointStyle: true,
          titleFont: { family: 'Inter', weight: '600' }, bodyFont: { family: 'Inter' },
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${opts.money ? money(ctx.parsed.y) : IDGPS.formatMoney(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { grid: { display: false }, border: { display: false }, ticks: { color: muted, font: { family: 'Inter', size: 12 } } },
        y: {
          beginAtZero: true, border: { display: false },
          grid: { color: css('--grid'), drawTicks: false },
          ticks: { color: muted, padding: 8, maxTicksLimit: 6, font: { family: 'Inter', size: 12 }, callback: v => (opts.money ? compact(v) : v), precision: 0 },
        },
      },
    };
  }

  function datasets(spec) {
    return spec.series.map(s => {
      const color = css(s.color);
      const surface = css('--surface');
      if (spec.type === 'line') {
        return {
          label: s.label, data: s.data, borderColor: color, borderWidth: 2, tension: .35, fill: true,
          backgroundColor: ctx => {
            const { chartArea, ctx: c } = ctx.chart;
            if (!chartArea) return 'transparent';
            const g = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            g.addColorStop(0, color + '33'); g.addColorStop(1, color + '00');
            return g;
          },
          pointRadius: 4, pointHoverRadius: 6, pointBackgroundColor: color, pointBorderColor: surface, pointBorderWidth: 2,
        };
      }
      return {
        label: s.label, data: s.data, backgroundColor: color, hoverBackgroundColor: color,
        borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: 'bottom',
        borderColor: surface, borderWidth: { top: 0, left: 1, right: 1 },
        maxBarThickness: 26, categoryPercentage: .7, barPercentage: .9,
      };
    });
  }

  function build(spec) {
    const canvas = document.getElementById(spec.el);
    if (!canvas || !window.Chart) return;
    const existing = charts.find(c => c.spec === spec);
    if (existing) existing.chart.destroy();
    const chart = new Chart(canvas, {
      type: spec.type,
      data: { labels: spec.labels, datasets: datasets(spec) },
      options: baseOptions(spec),
    });
    if (existing) existing.chart = chart; else charts.push({ spec, chart });
  }

  window.IDGPSCharts = { render: build };
  document.addEventListener('themechange', () => charts.forEach(c => build(c.spec)));
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => charts.forEach(c => build(c.spec)));
})();
