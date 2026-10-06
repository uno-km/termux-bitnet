/**
 * termux-bitnet - JavaScript / TypeScript API Bridge
 */
const { spawn } = require('child_process');

module.exports = {
  packageName: 'termux-bitnet',
  moduleName: 'termux_bitnet',
  runCli: function(args = []) {
    const pythonBin = process.env.PYTHON || 'python3';
    return spawn(pythonBin, ['-m', 'termux_bitnet', ...args], {
      stdio: 'inherit',
      env: process.env
    });
  }
};
