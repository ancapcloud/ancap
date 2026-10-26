const { getDefaultConfig } = require("expo/metro-config");

// Expo resolves npm workspaces and shared native modules automatically.
module.exports = getDefaultConfig(__dirname);
