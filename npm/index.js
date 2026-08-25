/**
 * @file index.js
 * @brief termux-bitnet Node.js / TypeScript Package Main Entry Point.
 */

const { BitNetEngine, detectHardware } = require('./lib/engine');
const { downloadModel, listModels, AVAILABLE_MODELS } = require('./lib/downloader');

function createEngine(options = {}) {
  return new BitNetEngine(options);
}

module.exports = {
  createEngine,
  BitNetEngine,
  detectHardware,
  downloadModel,
  listModels,
  AVAILABLE_MODELS,
};
