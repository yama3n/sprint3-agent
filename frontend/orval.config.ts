export default {
  api: {
    input: {
      target: '../backend/openapi.json',
    },
    output: {
      // タグごとにファイル分割: generated/{tag}.ts + 型は generated/model/
      // 例: import { useGetApplications } from '@/shared/api/generated/applications'
      mode: 'tags',
      target: './src/shared/api/generated',
      schemas: './src/shared/api/generated/model',
      // TanStack Query のフックを生成（features/*/api.ts が wrap して使う）
      client: 'react-query',
      httpClient: 'fetch',
      clean: true,
      prettier: true,
      // mutator は output 直下ではなく output.override 配下でないと無視され、
      // 生成コードが素の fetch() を呼んでしまう（Authorizationヘッダが付かない）
      override: {
        mutator: {
          path: './src/shared/api/mutator.ts',
          name: 'customInstance',
        },
      },
    },
  },
}
