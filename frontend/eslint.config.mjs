import nextPlugin from "eslint-config-next";

const eslintConfig = [
  ...nextPlugin,
  {
    ignores: ["src/shared/api/generated/**"],
  },
];

export default eslintConfig;
