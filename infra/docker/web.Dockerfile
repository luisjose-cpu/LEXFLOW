FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY apps/admin/package.json ./apps/admin/package.json
COPY apps/mobile/package.json ./apps/mobile/package.json
COPY packages/ui/package.json ./packages/ui/package.json
COPY packages/design-system/package.json ./packages/design-system/package.json
COPY packages/shared/package.json ./packages/shared/package.json
COPY packages/types/package.json ./packages/types/package.json

RUN npm ci

COPY . .

RUN npm --workspace apps/web run build

EXPOSE 3000
CMD ["sh", "-c", "npm --workspace apps/web run start -- -p ${PORT:-3000}"]
