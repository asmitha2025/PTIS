FROM nginx:1.27-alpine
COPY frontend /usr/share/nginx/html/frontend
COPY evidence /usr/share/nginx/html/evidence
EXPOSE 80
