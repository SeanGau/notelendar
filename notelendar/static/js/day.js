let previousContent = "";
$(".textarea.note-content, .textarea.note-key").on("focus", function (e) {
  previousContent = $(this).html();
  headerWidth = $("th.date")[0].clientWidth;
  thisOffset = $(this).offset().left;
  if (thisOffset < headerWidth) {
    $("#table-block").scrollLeft($("#table-block").scrollLeft() - headerWidth + thisOffset);
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

$(".textarea.note-key").on("blur", function (e) {
  header = $(this).html();
  header = header.replace(/(\r\n?|\n|\t)/g, "<br>");
  if (header == previousContent) {
    return;
  }
  if (header.replace("<br>", "").length < 1) {
    let dialog = confirm("空值會導致此欄位被移除，是否確定？");
    if (!dialog) {
      location.reload(true);
      return;
    } else {
      $(`table [data-note-key=${$(this).data('note-key')}]`).each(function () {
        $(this).parent("th, td").remove();
      })
    }
  }

  $.ajax({
    type: "POST",
    url: "/api/update-header",
    data: JSON.stringify({
      'key': $(this).data('note-key'),
      'value': header
    }),
    success: function () {
      console.log("success");
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      alert(XMLHttpRequest.status, XMLHttpRequest.readyState, textStatus);
    },
    contentType: "application/json"
  })
})

$("#add-col").on("click", function (e) {
  e.preventDefault();
  $.ajax({
    type: "POST",
    url: "/api/update-header",
    data: JSON.stringify({
      'value': $(".textarea.note-key").length
    }),
    success: function () {
      console.log("success");
      location.reload(true);
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

$("#search").on("click", function (e) {
  e.preventDefault();
  searchString = $("input[name=search]").val();
  sdate = $("input[name=sdate]").val();
  window.location.href = `/?search=${searchString}&sdate=${sdate}`;
})

$("select[name=freeze]").on("change", function(e) {
  e.preventDefault();
  //let freezeCol = url.searchParams.get("freeze") || 0;
  let freezeCol = $(this).val();
  $(".sticky").css({"left": ""});
  $(".sticky").removeClass("sticky");
  $("tr").each(function () {
    for (let i = 1; i <= freezeCol; i++) {
      let colDom = $($("td,th", this)[i]);
      colDom.css({"left": $("#table-block").scrollLeft() + colDom.offset().left});
      colDom.addClass("sticky");
    }
  })
})