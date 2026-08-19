/**
 * Opening-hours logic.
 *
 * The FACTS live in src/data/restaurant.ts. The WORKING OUT lives here. Keeping
 * them apart means editing hours never involves reading code — you only ever
 * touch the data file.
 */

export type Interval = { readonly opens: string; readonly closes: string };

export type DayKey =
  | 'monday'
  | 'tuesday'
  | 'wednesday'
  | 'thursday'
  | 'friday'
  | 'saturday'
  | 'sunday';

export type WeeklyHours = Readonly<Record<DayKey, readonly Interval[]>>;

export const DAY_ORDER: readonly DayKey[] = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
];

export const DAY_LABEL: Record<DayKey, string> = {
  monday: 'Monday',
  tuesday: 'Tuesday',
  wednesday: 'Wednesday',
  thursday: 'Thursday',
  friday: 'Friday',
  saturday: 'Saturday',
  sunday: 'Sunday',
};

export const DAY_SHORT: Record<DayKey, string> = {
  monday: 'Mon',
  tuesday: 'Tue',
  wednesday: 'Wed',
  thursday: 'Thu',
  friday: 'Fri',
  saturday: 'Sat',
  sunday: 'Sun',
};

/** "17:30" -> 1050 (minutes since midnight). Makes times comparable with < and >. */
function toMinutes(time: string): number {
  const [h, m] = time.split(':').map(Number);
  return h * 60 + m;
}

/** A moment in time, expressed the way opening hours are: a day and a clock time. */
export type Moment = { day: DayKey; minutes: number };

/**
 * What day and time is it IN WEYBRIDGE right now?
 *
 * This matters: a visitor in Dubai checking the site at 22:00 their time must be
 * told whether the restaurant is open in London, not where they are. The
 * timeZone option below does that regardless of the visitor's device settings.
 */
export function londonNow(now: Date = new Date()): Moment {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/London',
    weekday: 'long',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(now);

  const find = (type: string) => parts.find((p) => p.type === type)?.value ?? '';

  return {
    day: find('weekday').toLowerCase() as DayKey,
    minutes: Number(find('hour')) * 60 + Number(find('minute')),
  };
}

function previousDay(day: DayKey): DayKey {
  const i = DAY_ORDER.indexOf(day);
  return DAY_ORDER[(i + DAY_ORDER.length - 1) % DAY_ORDER.length];
}

function nextDay(day: DayKey): DayKey {
  const i = DAY_ORDER.indexOf(day);
  return DAY_ORDER[(i + 1) % DAY_ORDER.length];
}

/** True when an interval runs past midnight, e.g. 21:00 -> 01:00. */
function wrapsMidnight(interval: Interval): boolean {
  return toMinutes(interval.closes) <= toMinutes(interval.opens);
}

export type Status =
  | { open: true; closesAt: string }
  | { open: false; opensDay: DayKey; opensAt: string }
  | { open: false; opensDay: null; opensAt: null };

/** Is the restaurant open at this moment, and when does that change? */
export function statusAt(hours: WeeklyHours, at: Moment): Status {
  // Today's sittings.
  for (const interval of hours[at.day] ?? []) {
    const opens = toMinutes(interval.opens);
    const closes = toMinutes(interval.closes);
    if (wrapsMidnight(interval)) {
      if (at.minutes >= opens) return { open: true, closesAt: interval.closes };
    } else if (at.minutes >= opens && at.minutes < closes) {
      return { open: true, closesAt: interval.closes };
    }
  }

  // Still serving from last night — e.g. it is 00:30 and yesterday ran to 01:00.
  for (const interval of hours[previousDay(at.day)] ?? []) {
    if (wrapsMidnight(interval) && at.minutes < toMinutes(interval.closes)) {
      return { open: true, closesAt: interval.closes };
    }
  }

  // Closed. Find the next sitting, looking at today first, then up to a week ahead.
  const laterToday = (hours[at.day] ?? []).find((i) => toMinutes(i.opens) > at.minutes);
  if (laterToday) return { open: false, opensDay: at.day, opensAt: laterToday.opens };

  let day = at.day;
  for (let i = 0; i < 7; i++) {
    day = nextDay(day);
    const first = hours[day]?.[0];
    if (first) return { open: false, opensDay: day, opensAt: first.opens };
  }

  // No hours set at all anywhere in the week.
  return { open: false, opensDay: null, opensAt: null };
}

/** Turns a Status into the sentence a customer reads. */
export function statusLabel(status: Status, today: DayKey): string {
  if (status.open) return `Open now · until ${status.closesAt}`;
  if (status.opensDay === null) return 'Opening hours to be confirmed';
  if (status.opensDay === today) return `Closed · opens ${status.opensAt}`;
  if (status.opensDay === nextDay(today)) return `Closed · opens tomorrow ${status.opensAt}`;
  return `Closed · opens ${DAY_LABEL[status.opensDay]} ${status.opensAt}`;
}

/** "12:00–15:00, 17:00–23:00", or "Closed" for a day with no sittings. */
export function formatDay(intervals: readonly Interval[]): string {
  if (!intervals || intervals.length === 0) return 'Closed';
  return intervals.map((i) => `${i.opens}–${i.closes}`).join(', ');
}

export type HoursRow = { days: string; times: string };

/**
 * Collapses the week for display, so identical consecutive days become one row:
 * Mon–Fri 12:00–15:00, 17:00–23:00 / Sat 12:00–23:00 / Sun Closed
 */
export function weekRows(hours: WeeklyHours): HoursRow[] {
  const rows: HoursRow[] = [];
  let runStart: DayKey | null = null;
  let runEnd: DayKey | null = null;
  let runTimes = '';

  const flush = () => {
    if (!runStart || !runEnd) return;
    const days =
      runStart === runEnd
        ? DAY_SHORT[runStart]
        : `${DAY_SHORT[runStart]}–${DAY_SHORT[runEnd]}`;
    rows.push({ days, times: runTimes });
  };

  for (const day of DAY_ORDER) {
    const times = formatDay(hours[day] ?? []);
    if (times === runTimes && runStart) {
      runEnd = day;
    } else {
      flush();
      runStart = day;
      runEnd = day;
      runTimes = times;
    }
  }
  flush();

  return rows;
}
