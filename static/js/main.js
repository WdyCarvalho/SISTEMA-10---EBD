//CÓDIGO PARA FILTRAR TABELAS

// static/js/main.js

function filterTable(inputId, tableId) {
    // Pega o texto da caixa de busca e converte para maiúsculas
    var input = document.getElementById(inputId);
    var filter = input.value.toUpperCase();

    // Pega a tabela e as linhas (TR) dentro do corpo (TBODY)
    var table = document.getElementById(tableId);
    var tbody = table.getElementsByTagName("tbody")[0];
    var tr = tbody.getElementsByTagName("tr");

    // Loop por todas as linhas da tabela
    for (var i = 0; i < tr.length; i++) {
        // Pega todo o texto da linha
        var txtValue = tr[i].textContent || tr[i].innerText;

        // Compara o texto da linha com o filtro
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            tr[i].style.display = ""; // Mostra a linha se o texto for encontrado
        } else {
            tr[i].style.display = "none"; // Esconde a linha se não for encontrado
        }
    }
}