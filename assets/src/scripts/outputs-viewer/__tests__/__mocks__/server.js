import { rest } from "msw";
import { setupServer } from "msw/node";
import { fileList } from "../helpers/files";
import props, { publishUrl } from "../helpers/props";

export const handlers = [
  rest.get(props.filesUrl, (req, res, ctx) =>
    res(ctx.status(200), ctx.json({ files: fileList }))
  ),

  rest.get(fileList[0].url, (req, res, ctx) =>
    res(ctx.status(200), ctx.text("hello,world"))
  ),

  rest.post(publishUrl, (req, res, ctx) => res(ctx.status(200), ctx.json({}))),
];

const server = setupServer(...handlers);

export { server, rest };
