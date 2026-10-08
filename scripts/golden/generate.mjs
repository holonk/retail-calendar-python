// Generates reference ("golden") data from the JS retail-calendar package for the Python parity tests.
//
//   cd scripts/golden && npm ci && npm run generate
//
// The JS package does its date math in the host's local time, so its output depends on the timezone (DST shifts
// can move a year boundary by a week). The reference is the package running in UTC, which is what
// retail-calendar-api runs in. This script refuses to run in any other timezone.

import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { gzipSync } from 'node:zlib'
import { createRequire } from 'node:module'
import { createHash } from 'node:crypto'

const require = createRequire(import.meta.url)
const { RetailCalendarFactory, weekOfGregorianDate } = require('retail-calendar')
const { version } = require('retail-calendar/package.json')

if (Intl.DateTimeFormat().resolvedOptions().timeZone !== 'UTC' || new Date(2020, 6, 1).getTimezoneOffset() !== 0) {
  console.error('Run with TZ=UTC (npm run generate does this).')
  process.exit(1)
}

const outDir = process.argv[2]
if (!outDir) {
  console.error('usage: node generate.mjs <output directory>')
  process.exit(1)
}
mkdirSync(outDir, { recursive: true })

const fmt = (date) => date.toISOString().slice(0, 10)
const range = (start, end) => Array.from({ length: end - start + 1 }, (_, i) => start + i)
const nullable = (value) => (value === -1 ? null : value)

const WEEK_CALCULATIONS = [0, 1, 2, 3, 4] // every strategy except CustomLeapYear, which takes its own parameters
const CUSTOM_LEAP_YEARS = [
  { leapYear: 2005, leapYearEndDate: '2006-03-11', leapYearFrequency: 6 },
  { leapYear: 2018, leapYearEndDate: '2019-02-02', leapYearFrequency: 5 },
  { leapYear: 2023, leapYearEndDate: '2024-02-03', leapYearFrequency: 7 },
]
const LAST_DAYS_OF_WEEK = range(1, 7)
const LAST_MONTHS_OF_YEAR = range(0, 11)

function writeGzip(name, content) {
  writeFileSync(join(outDir, name), gzipSync(content, { level: 9 }))
  console.log(`wrote ${name}`)
}

// 1. Year boundaries: number of weeks and first day for every strategy, week end day, year end month and year.
//    Week grouping, addLeapWeekToMonth and beginningMonthIndex do not affect boundaries.
function boundaries() {
  const rows = ['week_calculation,custom_leap_year,last_day_of_week,last_month_of_year,year,number_of_weeks,first_day']
  const add = (options, custom, year) => {
    const calendar = new RetailCalendarFactory(options, year)
    const { weekCalculation, lastDayOfWeek, lastMonthOfYear } = options
    rows.push(
      [weekCalculation, custom, lastDayOfWeek, lastMonthOfYear, year, calendar.numberOfWeeks,
        fmt(calendar.weeks[0].gregorianStartDate)].join(','),
    )
  }
  for (const weekCalculation of WEEK_CALCULATIONS)
    for (const lastDayOfWeek of LAST_DAYS_OF_WEEK)
      for (const lastMonthOfYear of LAST_MONTHS_OF_YEAR)
        for (const year of range(1950, 2060))
          add({ weekGrouping: 2, weekCalculation, lastDayOfWeek, lastMonthOfYear }, '', year)
  CUSTOM_LEAP_YEARS.forEach((custom, index) => {
    for (const lastMonthOfYear of [1, 11])
      for (const year of range(1950, 2060))
        add({ weekGrouping: 2, weekCalculation: 5, lastDayOfWeek: 6, lastMonthOfYear, ...custom }, index, year)
  })
  writeGzip('boundaries.csv.gz', rows.join('\n') + '\n')
}

// 2. Every field of every week, month and day, for a grid of configurations.
function detailConfigs() {
  const configs = []
  const strategies = [...WEEK_CALCULATIONS.map((weekCalculation) => ({ weekCalculation })),
    { weekCalculation: 5, ...CUSTOM_LEAP_YEARS[0] }]
  const weekEnds = [[6, 0], [7, 9], [5, 11], [1, 7]] // [lastDayOfWeek, lastMonthOfYear]
  for (const strategy of strategies)
    for (const weekGrouping of [0, 1, 2])
      for (const addLeapWeekToMonth of [undefined, 0, 10, 11])
        for (const beginningMonthIndex of [undefined, 0])
          for (const [lastDayOfWeek, lastMonthOfYear] of weekEnds) {
            const options = { weekGrouping, lastDayOfWeek, lastMonthOfYear, ...strategy }
            if (addLeapWeekToMonth !== undefined) options.addLeapWeekToMonth = addLeapWeekToMonth
            if (beginningMonthIndex !== undefined) options.beginningMonthIndex = beginningMonthIndex
            configs.push(options)
          }
  return configs
}

function serialize(calendar, withDays) {
  const data = {
    numberOfWeeks: calendar.numberOfWeeks,
    weeks: calendar.weeks.map((w) => [w.weekOfYear, nullable(w.weekOfMonth), nullable(w.weekOfQuarter),
      nullable(w.monthOfYear), nullable(w.quarterOfYear), fmt(w.gregorianStartDate), fmt(w.gregorianEndDate)]),
    months: calendar.months.map((m) => [m.monthOfYear, m.quarterOfYear, m.numberOfWeeks, m.weeks.length,
      fmt(m.gregorianStartDate), fmt(m.gregorianEndDate)]),
  }
  if (withDays) {
    data.days = calendar.days.map((d) => [fmt(d.gregorianStartDate), fmt(d.gregorianEndDate), d.dayOfYear,
      d.dayOfWeek, nullable(d.dayOfMonth), d.weekOfYear, nullable(d.monthOfYear), d.gregorianMonthOfYear,
      d.gregorianDayOfYear, d.gregorianDayOfMonth])
  }
  return data
}

// Full detail of one year (a 53-week year for most configurations) of every configuration, so a mismatch is easy
// to read. Days only where the leap week options are unset, to keep the file small; the digests cover the rest.
function calendars(configs) {
  const out = []
  configs.forEach((options, config) => {
    const withDays = options.addLeapWeekToMonth === undefined && options.beginningMonthIndex === undefined
    out.push({ config, year: 2023, ...serialize(new RetailCalendarFactory(options, 2023), withDays) })
  })
  writeGzip('calendars.json.gz', JSON.stringify(out))
}

// A digest of every week, month and day for many more years. The Python tests serialize their calendars the same
// way (compact JSON) and compare the first 16 hex digits of its SHA-256.
function digests(configs) {
  const rows = ['config,year,digest']
  configs.forEach((options, config) => {
    for (const year of range(2000, 2050)) {
      const json = JSON.stringify(serialize(new RetailCalendarFactory(options, year), true))
      rows.push([config, year, createHash('sha256').update(json).digest('hex').slice(0, 16)].join(','))
    }
  })
  writeGzip('digests.csv.gz', rows.join('\n') + '\n')
}

// 3. weekOfGregorianDate (what retail-calendar-api's get-date-segments-from-dates uses) on random dates.
function lookups(configs) {
  let seed = 20261008 // deterministic linear congruential generator, so the output is reproducible
  const random = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648)
  const start = Date.UTC(1990, 0, 1)
  const days = (Date.UTC(2050, 11, 31) - start) / 86400000
  const rows = ['config,date,year,week']
  for (let i = 0; i < 20000; i++) {
    const configIndex = Math.floor(random() * configs.length)
    const date = new Date(start + Math.floor(random() * (days + 1)) * 86400000)
    const { calendar, week } = weekOfGregorianDate(date, configs[configIndex])
    rows.push([configIndex, fmt(date), calendar.year, week.weekOfYear].join(','))
  }
  writeGzip('lookups.csv.gz', rows.join('\n') + '\n')
  writeFileSync(join(outDir, 'configs.json'), JSON.stringify(configs, null, 1) + '\n')
  console.log('wrote configs.json')
}

const configs = detailConfigs()
boundaries()
calendars(configs)
digests(configs)
lookups(configs)
writeFileSync(join(outDir, 'SOURCE.txt'),
  `Generated by scripts/golden/generate.mjs from retail-calendar@${version} running in TZ=UTC.\n`)
