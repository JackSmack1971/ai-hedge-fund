/* eslint-disable no-console */

export const debugLog: (...args: unknown[]) => void = import.meta.env.DEV
  ? console.log.bind(console)
  : () => {};
