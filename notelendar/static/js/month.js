let previousContent = "";

$(".textarea-box").on("focus", ".textarea.note-content", function (e) {
  $("#table-block table").addClass("editing");
  previousContent = $(this).html();
})

$(".textarea-box").on("blur", ".textarea.note-content", function (e) {
  $("#table-block table").removeClass("editing");
  noteDate = $(this).data('note-date');
  noteKey = $(this).data('note-key');
  note = $(this).html();
  if (note == previousContent) {
    return;
  }
  $.ajax({
    type: "POST",
    url: "/api/update-content",
    data: JSON.stringify({
      'noteDate': noteDate,
      'noteKey': noteKey,
      'note': note
    }),
    success: function () {
      console.log("success");
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      alert(XMLHttpRequest.status, XMLHttpRequest.readyState, textStatus);
    },
    contentType: "application/json"
  });
})

const url = new URL(window.location.href);

$("#prev-dates").on("click", function (e) {
  e.preventDefault();
  let nowPage = url.searchParams.get("page") || 0;
  url.searchParams.set("page", Number(nowPage) - 1);
  window.location.href = url.href;
})

$("#next-dates").on("click", function (e) {
  e.preventDefault();
  let nowPage = url.searchParams.get("page") || 0;
  url.searchParams.set("page", Number(nowPage) + 1);
  window.location.href = url.href;
})

$("#headers-checkgroup input[type=checkbox]").on("change", function (e) {
  e.preventDefault();
  let displayCol = JSON.parse(localStorage.getItem('month_display_col') || '[]');
  key = $(this).val();
  if ($(this).prop("checked")) {
    $(`.textarea[data-note-key=${key}]`).removeClass("d-none");
    displayCol = displayCol.filter(function (value) {
      return value != key;
    });
  } else {
    $(`.textarea[data-note-key=${key}]`).addClass("d-none");
    displayCol.push(key);
  }
  localStorage.setItem('month_display_col', JSON.stringify(displayCol));
})

let displayCol = JSON.parse(localStorage.getItem('month_display_col') || '[]');
displayCol.forEach(key => {
  $(`.textarea[data-note-key=${key}]`).addClass("d-none");
  $(`#headers-checkgroup [value=${key}]`).prop("checked", false);
})

$(".week td .textarea").on("wheel", function (e) {
  e.stopPropagation();
})

$(".week td").on("wheel", function (e) {
  e.stopPropagation();
})

const addNoteModal = new bootstrap.Modal('#addNoteModal');
$(".week td, .week td .textarea").on("click", function (e) {
  date = $(".textarea-box", $(this)).data("note-date");
  $("#addNoteModal input[name=addNoteDate]").val(date);
  key = $(this).data("note-key") || $("#addNoteModal select[name=addNoteKey]").val();
  $("#addNoteModal select[name=addNoteKey]").val(key);
  note = $(`.textarea[data-note-key=${key}]`, $(this)).html() || "";
  $("#addNoteModal .textarea[name=addNoteValue]").html(`<div class="spinner-border text-secondary" role="status"><span class="visually-hidden">Loading...</span></div>`);
  $("#addNoteModal .textarea[name=addNoteValue]").html(note);
  addNoteModal.show();
})

$("#addNoteModal #submit").on("click", function (e) {
  noteDate = $("#addNoteModal input[name=addNoteDate]").val();
  noteKey = $("#addNoteModal select[name=addNoteKey]").val();
  note = $("#addNoteModal .textarea[name=addNoteValue]").html();
  $.ajax({
    type: "POST",
    url: "/api/update-content",
    data: JSON.stringify({
      'noteDate': noteDate,
      'noteKey': noteKey,
      'note': note
    }),
    success: function () {
      console.log("success");
      addNoteModal.hide();
      location.reload(true);
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      alert(XMLHttpRequest.status, XMLHttpRequest.readyState, textStatus);
    },
    contentType: "application/json"
  });
})

$("#addNoteModal select, #addNoteModal input").on("change", function (e) {
  noteDate = $("#addNoteModal input[name=addNoteDate]").val();
  noteKey = $("#addNoteModal select[name=addNoteKey]").val();
  $("#addNoteModal .textarea[name=addNoteValue]").html(`<div class="spinner-border text-secondary" role="status"><span class="visually-hidden">Loading...</span></div>`);
  $("#addNoteModal .textarea[name=addNoteValue]").prop("contenteditable", false);

  $.getJSON(`/api/get-content/${noteDate}/${noteKey}`, function (data) {
    $("#addNoteModal .textarea[name=addNoteValue]").html(data['note']);

  }).fail(function (XMLHttpRequest, textStatus, errorThrown) {
    alert(XMLHttpRequest.status, XMLHttpRequest.readyState, textStatus);

  }).always(function () {
    $("#addNoteModal .textarea[name=addNoteValue]").prop("contenteditable", true);
  })
})