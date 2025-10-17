export const formatDuration = (minutes: number) => {
  if (!minutes || minutes <= 0) {
    return '0 min'
  }

  const hours = Math.floor(minutes / 60)
  const remaining = minutes % 60

  if (hours === 0) {
    return `${minutes} min`
  }

  if (remaining === 0) {
    return `${hours} hr`
  }

  return `${hours} hr ${remaining} min`
}
