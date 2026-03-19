// @ts-nocheck
import * as __fd_glob_26 from "../content/docs/getting-started/rate-limits.mdx?collection=docs"
import * as __fd_glob_25 from "../content/docs/getting-started/rate-limits.cn.mdx?collection=docs"
import * as __fd_glob_24 from "../content/docs/getting-started/quickstart.mdx?collection=docs"
import * as __fd_glob_23 from "../content/docs/getting-started/quickstart.cn.mdx?collection=docs"
import * as __fd_glob_22 from "../content/docs/getting-started/authentication.mdx?collection=docs"
import * as __fd_glob_21 from "../content/docs/getting-started/authentication.cn.mdx?collection=docs"
import * as __fd_glob_20 from "../content/docs/api-reference/strategies.mdx?collection=docs"
import * as __fd_glob_19 from "../content/docs/api-reference/portfolio.mdx?collection=docs"
import * as __fd_glob_18 from "../content/docs/api-reference/orders.mdx?collection=docs"
import * as __fd_glob_17 from "../content/docs/api-reference/markets.mdx?collection=docs"
import * as __fd_glob_16 from "../content/docs/api-reference/data-sports.mdx?collection=docs"
import * as __fd_glob_15 from "../content/docs/api-reference/data-nba.mdx?collection=docs"
import * as __fd_glob_14 from "../content/docs/api-reference/data-btc.mdx?collection=docs"
import * as __fd_glob_13 from "../content/docs/api-reference/auth.mdx?collection=docs"
import * as __fd_glob_12 from "../content/docs/api-reference/analysis.mdx?collection=docs"
import * as __fd_glob_11 from "../content/docs/guides/nba-fusion-trading.mdx?collection=docs"
import * as __fd_glob_10 from "../content/docs/guides/convergence-arbitrage.mdx?collection=docs"
import * as __fd_glob_9 from "../content/docs/guides/btc-multiframe.mdx?collection=docs"
import * as __fd_glob_8 from "../content/docs/index.mdx?collection=docs"
import * as __fd_glob_7 from "../content/docs/index.cn.mdx?collection=docs"
import * as __fd_glob_6 from "../content/docs/changelog.mdx?collection=docs"
import { default as __fd_glob_5 } from "../content/docs/getting-started/meta.json?collection=docs"
import { default as __fd_glob_4 } from "../content/docs/getting-started/meta.cn.json?collection=docs"
import { default as __fd_glob_3 } from "../content/docs/guides/meta.json?collection=docs"
import { default as __fd_glob_2 } from "../content/docs/api-reference/meta.json?collection=docs"
import { default as __fd_glob_1 } from "../content/docs/meta.json?collection=docs"
import { default as __fd_glob_0 } from "../content/docs/meta.cn.json?collection=docs"
import { server } from 'fumadocs-mdx/runtime/server';
import type * as Config from '../source.config';

const create = server<typeof Config, import("fumadocs-mdx/runtime/types").InternalTypeConfig & {
  DocData: {
  }
}>({"doc":{"passthroughs":["extractedReferences"]}});

export const docs = await create.docs("docs", "content/docs", {"meta.cn.json": __fd_glob_0, "meta.json": __fd_glob_1, "api-reference/meta.json": __fd_glob_2, "guides/meta.json": __fd_glob_3, "getting-started/meta.cn.json": __fd_glob_4, "getting-started/meta.json": __fd_glob_5, }, {"changelog.mdx": __fd_glob_6, "index.cn.mdx": __fd_glob_7, "index.mdx": __fd_glob_8, "guides/btc-multiframe.mdx": __fd_glob_9, "guides/convergence-arbitrage.mdx": __fd_glob_10, "guides/nba-fusion-trading.mdx": __fd_glob_11, "api-reference/analysis.mdx": __fd_glob_12, "api-reference/auth.mdx": __fd_glob_13, "api-reference/data-btc.mdx": __fd_glob_14, "api-reference/data-nba.mdx": __fd_glob_15, "api-reference/data-sports.mdx": __fd_glob_16, "api-reference/markets.mdx": __fd_glob_17, "api-reference/orders.mdx": __fd_glob_18, "api-reference/portfolio.mdx": __fd_glob_19, "api-reference/strategies.mdx": __fd_glob_20, "getting-started/authentication.cn.mdx": __fd_glob_21, "getting-started/authentication.mdx": __fd_glob_22, "getting-started/quickstart.cn.mdx": __fd_glob_23, "getting-started/quickstart.mdx": __fd_glob_24, "getting-started/rate-limits.cn.mdx": __fd_glob_25, "getting-started/rate-limits.mdx": __fd_glob_26, });