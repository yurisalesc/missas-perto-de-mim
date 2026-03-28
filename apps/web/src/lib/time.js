export function weekdayNamePt(date = new Date()) {
  const names = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
  ];
  return names[(date.getDay() + 6) % 7];
}
