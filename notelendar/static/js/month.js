let previousContent = "";

$(".textarea.note-content").on("focus", function (e) {
  previousContent = $(this).html();
  thisOffset = $(this).offset().left;
  if (thisOffset < 0) {
    $("#table-block").scrollLeft($("#table-block").scrollLeft() + thisOffset);
  }
})

$(".textarea.note-content").on("blur", function (e) {
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

$("#header-key").on("change", function (e) {
  e.preventDefault();
  nextKey = $(this).val();
  url.searchParams.set("key", nextKey);
  window.location.href = url.href;
})