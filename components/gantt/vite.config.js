import { resolve } from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
	build: {
		lib: {
			entry: resolve(__dirname, 'src/index.js'),
			name: 'Gantt',
			fileName: 'nxenv-gantt',
		},
		rollupOptions: {
			output: {
				format: 'cjs',
				assetFileNames: 'nxenv-gantt[extname]',
				entryFileNames: 'nxenv-gantt.[format].js',
			},
		},
	},
	output: { interop: 'auto' },
	server: { watch: { include: ['dist/*', 'src/*'] } },
});
