# Content Review Squad (TS)

This project is configured to use **Node.js 24** with native TypeScript support.

## Prerequisites
- Node.js v24.12.0 or higher (see `.nvmrc`)

## Setup
```bash
npm install
```

## Running the project
Node 24 allows running TypeScript files directly using the `--experimental-strip-types` flag (which is faster than using `ts-node` or `tsx` for execution).

```bash
# Start the project
npm start

# Development mode (with watch)
npm run dev
```

## Configuration
- `package.json`: Set to `"type": "module"` and uses `node --experimental-strip-types`.
- `tsconfig.json`: Configured for `NodeNext` resolution and ESM.
