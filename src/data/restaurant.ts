import type { WeeklyHours } from '../lib/hours';

/**
 * THE SINGLE SOURCE OF TRUTH.
 *
 * Every phone number, address, email and opening time on this website comes from
 * this file. Nothing is typed by hand into a page — that is precisely the mistake
 * the current la-casa-weybridge.com makes, and why it now tells customers two
 * different closing times.
 *
 * To change something on the live site: edit the line here, save, commit. Done.
 */

/**
 * ⚠️ OPENING HOURS ARE NOT YET CONFIRMED BY THE CLIENT. ⚠️
 *
 * The current website contradicts itself:
 *   - its booking page says  Mon–Fri 12:00–15:00 and 17:00–23:00, Sat 12:00–23:00
 *   - its homepage + footer say  Mon–Sat 17:00–22:00
 *   - Sunday is not stated anywhere we have seen
 *
 * The booking page version is used below because it is the more specific of the
 * two. It is a PLACEHOLDER. Get the real hours from the owner in writing, put
 * them here, then set hoursConfirmed to true.
 */
export const hoursConfirmed = false;

const lunchAndDinner = [
  { opens: '12:00', closes: '15:00' },
  { opens: '17:00', closes: '23:00' },
] as const;

export const hours: WeeklyHours = {
  monday: lunchAndDinner,
  tuesday: lunchAndDinner,
  wednesday: lunchAndDinner,
  thursday: lunchAndDinner,
  friday: lunchAndDinner,
  saturday: [{ opens: '12:00', closes: '23:00' }],
  // TODO: confirm. Sunday is guessed as closed — no source states it either way.
  sunday: [],
};

export const restaurant = {
  name: 'La Casa',
  legalName: 'La Casa Restaurant & Grill',
  tagline: 'Italian restaurant & grill',

  // Written out once, in the exact form it must appear everywhere — including
  // their Google Business Profile. Inconsistent name/address/phone across the web
  // is one of the things that weakens local search results.
  phone: '01932 843470',
  // The same number with no spaces and a country code, for tap-to-dial on a phone.
  phoneHref: '+441932843470',
  email: 'la.casa@btconnect.com',

  address: {
    street: '2 Monument Hill',
    town: 'Weybridge',
    county: 'Surrey',
    postcode: 'KT13 8RH',
    country: 'GB',
  },

  // Used by the "Get directions" link and, in Phase 8, the map embed.
  googleMapsUrl: 'https://www.google.com/maps/search/?api=1&query=La+Casa+2+Monument+Hill+Weybridge+KT13+8RH',

  hours,
  hoursConfirmed,

  /**
   * Takeaway platforms. Left empty until the client gives us their real listing
   * URLs — a guessed link that lands on the wrong restaurant is worse than none.
   * Phase 6 renders whichever of these are filled in and hides the rest.
   */
  delivery: {
    deliveroo: '',
    justEat: '',
    uberEats: '',
  },
} as const;
