/**
 * @file index.js
 * @brief termux-bitnet Node.js / TypeScript Package Main Entry Point.
 */

const { BitNetEngine, detectHardware } = require('./lib/engine');

function createEngine(options = {}) {
  return new BitNetEngine(options);
}

module.exports = {
  createEngine,
  BitNetEngine,
  detectHardware,
};
