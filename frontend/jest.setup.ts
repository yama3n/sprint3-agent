import "@testing-library/jest-dom";

// jsdomのテスト環境はFetch APIを持たない（Node組み込みのfetchはjsdomのvmサンドボックスに
// 伝播しない）。jest.spyOn(global, "fetch") 等が動くよう最小限のpolyfillを当てる。
// ESM importはホイストされ実行順を保証できないため、依存順が重要なここはrequireで明示する
// （undiciがモジュール読み込み時にglobalThis.TextDecoderを参照するため、先に補う必要がある）。
const { TextDecoder, TextEncoder } = require("node:util");
const { ReadableStream, WritableStream, TransformStream } = require("node:stream/web");
const { MessageChannel, MessagePort } = require("node:worker_threads");
Object.assign(globalThis, {
  TextEncoder,
  TextDecoder,
  ReadableStream,
  WritableStream,
  TransformStream,
  MessageChannel,
  MessagePort,
});

const { fetch, Headers, Request, Response, FormData, Blob } = require("undici");
Object.assign(globalThis, { fetch, Headers, Request, Response, FormData, Blob });
