document.addEventListener('DOMContentLoaded', function () {
    const Toast = Swal.mixin({
        toast: true,
        position: 'bottom-end',
        iconColor: 'white',
        customClass: {
            popup: 'colored-toast',
        },
        showConfirmButton: false,
        timer: 5000,
        timerProgressBar: true,
    })

    document.addEventListener("htmx:confirm", function(e) {
        if (!e.detail.question) return
        e.preventDefault()
        Swal.fire({
            title: "¿Realmente deseas continuar?",
            text: e.detail.question,
            showCancelButton: true,
            confirmButtonText: "Aceptar",
            cancelButtonText: "Cancelar",
            }).then(function(result) {
                if (result.isConfirmed) {
                e.detail.issueRequest(true);
            }
        })
    });

    document.addEventListener("toast:deleted", function(e) {
        Toast.fire({
            icon: 'success',
            title: 'Registro eliminado exitosamente.'
        });
    });

    document.addEventListener("toast:updated", function(e) {
        Toast.fire({
            icon: 'success',
            title: 'Registro actualizado exitosamente.'
        });
    });

    document.addEventListener("toast:created", function(e) {
        Toast.fire({
            icon: 'success',
            title: 'Registro creado exitosamente.'
        });
    });

    document.addEventListener("toast:synced", function(e) {
        Toast.fire({
            icon: 'success',
            title: 'Metadatos de la base de datos han sido sincronizados exitosamente.'
        });
    });

    document.addEventListener("toast:synced", function(e) {
        Toast.fire({
            icon: 'success',
            title: 'Metadatos de la base de datos han sido sincronizados exitosamente.'
        });
    });

    document.addEventListener("toasts:error", function(e) {
        Toast.fire({
            icon: 'error',
            title: e.detail.message || 'Ocurrió un error.'
        });
    });
});