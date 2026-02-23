export function formatWon(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 100_000_000) {
    return `${sign}${(abs / 100_000_000).toFixed(1)}억원`;
  }
  if (abs >= 10_000) {
    return `${sign}${Math.round(abs / 10_000).toLocaleString()}만원`;
  }
  return `${value.toLocaleString()}원`;
}

export function formatPopulation(value: number): string {
  if (value >= 10_000) {
    return `${(value / 10_000).toFixed(1)}만명`;
  }
  return `${value.toLocaleString()}명`;
}

export function formatNumber(value: number): string {
  return value.toLocaleString("ko-KR");
}
