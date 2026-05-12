const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = (env, argv) => {
  const isDev = argv.mode === 'development';

  return {
    entry: './src/renderer/app.js',
    target: 'web',
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: 'bundle.js',
      clean: true
    },
    module: {
      rules: [
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env', '@babel/preset-react']
            }
          }
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader']
        },
        {
          test: /\.(png|jpg|jpeg|gif|ico|svg)$/,
          type: 'asset/resource'
        }
      ]
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/renderer/index.html',
        title: 'ScoobyBench'
      })
    ],
    resolve: {
      extensions: ['.js', '.jsx']
    },
    devServer: {
      port: 3000,
      hot: true,
      historyApiFallback: true
    },
    devtool: isDev ? 'source-map' : false
  };
};
