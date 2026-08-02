# Этап 1: Сборка статики Node.js
FROM node:18-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Этап 2: Продакшн-контур Nginx
FROM nginx:stable-alpine
# Копируем скомпилированные файлы из предыдущего этапа в системную папку Nginx
COPY --from=build-stage /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]