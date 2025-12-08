# Clean up project API container
FROM golang:1.20-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o /bin/cleaner

FROM alpine:3.18
COPY --from=builder /bin/cleaner /bin/cleaner
EXPOSE 8080
CMD ["/bin/cleaner"]
