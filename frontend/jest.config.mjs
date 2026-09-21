import nextJest from "next/jest.js";

const createJestConfig = nextJest({ dir: "./" });

/** @type {import('jest').Config} */
const config = {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  // undiciのFetch polyfillがハンドルを掴んだままになりjestが終了しないため強制終了する
  // （テスト自体は完走している。個別ファイル実行時のハング防止）
  forceExit: true,
};

export default createJestConfig(config);
