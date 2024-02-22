const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const WebpackShellPluginNext = require('webpack-shell-plugin-next');
const WatchExternalFilesPlugin = require("webpack-watch-files-plugin").default;

const resolvable = (...segments) => {
  return (...ps) => {
    return path.resolve(__dirname, ...segments, ...ps);
  };
}

const PATHS = {
  SRC: resolvable('src'),
  DIST: resolvable('dist'),
  SITE: resolvable('site'),
  RES: resolvable('src/res'),
  TPL: resolvable('src/tpl'),
  LANG: resolvable('lang'),
}

const LANGS = ['it', 'en', 'es'];

const buildPages = (root, stringdir, langs = [], templates = []) => {
  let langsarg = '';
  if (langs.length) {
    langsarg = `-l ${langs.join(',')}`;
  }
  tplargs = templates.map(tpl => `-t ${tpl}`).join(' ');
  return `python3 ./make-pages.py -s ${stringdir} ${tplargs} ${langsarg} ${root} ${PATHS.DIST()}`;
}

module.exports = (env, mode) => {
  const DEV = mode === 'development';

  return {
    entry: PATHS.SRC('index.js'),

    output: {
      filename: '[name].js',
      path: PATHS.DIST(),
    },

    resolve: {
      extensions: ['.js', '.scss'],
      alias: {
        '@': PATHS.SRC(),
      }
    },

    module: {
      rules: [
        // JS
        // { test: /\.js$/, use: [
        //   { loader: 'babel-loader', options: {
        //     sourceMaps: true,
        //   }},
        // ]},

        // STYLE
        { test: /\.scss$/, use: [
          DEV ? 'style-loader' : MiniCssExtractPlugin.loader,
          { loader: 'css-loader', options: {
            url: false,
          }},
          { loader: 'sass-loader', options: {
            sourceMap: true,
          }}
        ]},
      ]
    },

    plugins: [
      new MiniCssExtractPlugin({
        filename: '[name].css',
      }),

      new CopyWebpackPlugin({
        patterns: [{
          from: PATHS.RES(),
          to: PATHS.DIST(),
          globOptions: {
            ignore: ['.*']
          },
        }]
      }),

      new WebpackShellPluginNext({
        onAfterDone:{
          scripts: [
            buildPages(PATHS.SITE(), PATHS.LANG(), LANGS, [PATHS.TPL()])
          ],
          blocking: false,
          parallel: true
        }
      }),

      new WatchExternalFilesPlugin({
        files: [
          PATHS.SITE('**/*.html.jinja'),
          PATHS.SITE('**/*.yml'),
          PATHS.LANG('**/*.json'),
          PATHS.TPL('**/*.html.jinja'),
        ]
      })
    ]
  }
};