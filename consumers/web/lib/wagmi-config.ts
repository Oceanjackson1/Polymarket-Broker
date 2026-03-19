import { http, cookieStorage, createStorage } from "wagmi";
import { polygon } from "wagmi/chains";
import { getDefaultConfig } from "@rainbow-me/rainbowkit";

const projectId =
  process.env.NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID || "placeholder_build_id";

export const config = getDefaultConfig({
  appName: "Polymarket Broker",
  projectId,
  chains: [polygon],
  transports: {
    [polygon.id]: http(),
  },
  ssr: true,
  storage: createStorage({
    storage: cookieStorage,
  }),
});
