FROM node:22-alpine

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@10.0.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/studio/package.json apps/studio/package.json

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm --filter @awe/studio build

EXPOSE 3000

CMD ["pnpm", "--filter", "@awe/studio", "start"]