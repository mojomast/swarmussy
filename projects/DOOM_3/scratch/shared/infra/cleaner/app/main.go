package main

import (
    "fmt"
    "log"
    "net/http"
)

func main() {
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        fmt.Fprintln(w, "healthy")
    })

    http.HandleFunc("/cleanup", func(w http.ResponseWriter, r *http.Request) {
        // Placeholder: real cleanup logic would go here
        w.WriteHeader(http.StatusOK)
        fmt.Fprintln(w, "cleanup started")
    })

    log.Println("Starting CleanUp API on :8080")
    if err := http.ListenAndServe(":8080", nil); err != nil {
        log.Fatal(err)
    }
}
