module.exports = {
  buildCommand: 'cd frontend && npm ci && npm run build',
  outputDirectory: 'frontend/build',
  nodeVersion: '18',
  environment: 'production',
  installCommand: 'cd frontend && npm ci'
};
