(function (exports, ng, $) {
    'use strict';

    /**
     * @var Object box
     */
    var box = ng.module('box', ['ngResource', 'ui.router', 'infinite-scroll', 'ngSanitize']);
    exports.box = box;
	
	/* Repeat directive that activates tooltip  on loaded devices for device info on mouseover*/
	box.directive('deviceRepeatDirective', function ($compile, $timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attr) {
                if (scope.$last === true) {
                    $timeout(function () {
                        scope.$emit('deviceRepeatDirective');
                        /*var is_touch_device = 'ontouchstart' in document.documentElement;
						if(!is_touch_device && window.matchMedia("(min-width: 981px)").matches) {
	                        $(".device").tooltip();
                        }*/
                        //element.append('<li class="divider"></li><li id="allDevices" class="device active"><a href="javascript:void(0)" ng-click="infinity.nextPage(-1)">All devices</a></li>');
						var template = '<li class="divider"></li><li id="allDevices" class="device active"><a href="javascript:void(0)" ng-click="infinity.nextPage(-1)">All devices</a></li>';
			            var linkFn = $compile(template);
			            var content = linkFn(scope);
			            element.parent().append(content); 

						$('#deviceDropdown').bind("click", function()
						{
						  $('#deviceDropdown').delay(500).fadeOut(600); //$('#select'), not ('#select')
						});


                    });
                }
            }
        }
     });

	/* Repeat directive that manages thumbnail repeats */
	box.directive('thumbnailRepeatDone', function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attr) {
                if (scope.$last === true) {
                    $timeout(function () {
                        //scope.$emit('thumbnailRepeatDirective');
                        eval(attr.thumbnailRepeatDone);
                    });
                }
            }
        }
     });
	
	// Infinity constructor function to encapsulate HTTP and pagination logic
	box.factory('Infinity', function($http) {
	  var Infinity = function($scope) {
	  	this.publish = $scope;
	    this.busy = false;
	    this.page = 1;
		this.device = -1; 
		this.type = null; 
		this.lastCount = -1; 
		this.filters = [];
		this.photolist = new Object();
		this.price = 0.11;
		this.shipping = 5;

		this.imageCount = -1; 
		this.device_info = null;
	};

	  // Todo, move this from infinity to device 
	  Infinity.prototype.editDevice = function(device) {
		  $('#deviceDetailModal').attr("device", device);					  
		  $.ajax({
			    url : "/device/detail?id="+device,
				async: false,
				context: this,
			    success : function(result){
			        $("#deviceDetailModalInput").attr("value", result.product_name);
			        //$('#deviceDetailModal').modal('show');				
			        this.device_info = result; 
			        $("#device-message").remove();
			        if(this.device != -1) {
			        	var last_backup = new Date(this.device_info.last_backup*1000);
						var last_backup_string = ""; 
						
						if(this.device_info.last_backup > 0) {
							last_backup_string = "Last backup of this device was: "+ (last_backup.getYear()+1900)+"-"+ ('0' + last_backup.getMonth()).slice(-2)+"-"+('0' + last_backup.getDate()).slice(-2);
						}

			        	$("#infiniteContainer").before("<div id='device-message' style='background-color: #DDD; padding: 5px; padding-left: 15px; margin-bottom: 10px;  '><div style='float: left;'><b>"+this.device_info.product_name+"</b> (<a href='#' onClick=\"$('#deviceDetailModal').modal('show')\">Change name</a>) – "+this.device_info.image_count+" images and "+this.device_info.video_count+" videos. "+last_backup_string+"</div><div style='float: right;'></div><br style='clear:both;' /></div>");
			        }
			    }
		  });	  	
	  }

	  // Todo, move this from infinity to device 
	  Infinity.prototype.updateDevice = function() {
		$.ajax({
		    url : "/device/update?id="+$('#deviceDetailModal').attr("device")+"&product_name="+$("#deviceDetailModalInput").val(),
			async: false,
			context: this,
		    success : function(result){
		        window.location = "/"; 
		    }
		});	  	
	  }

	  Infinity.prototype.nextCheckoutStep = function(){
		this.publish.checkoutstep++;
	  }

	  Infinity.prototype.nextCheckoutStep = function(){
		this.publish.checkoutstep++;
	  }

	  Infinity.prototype.selectTab = function(state){
		this.publish.state = state;
	  }

	  Infinity.prototype.updateCart = function(event){
		this.price = event.target.attributes.price.value;
		$(".photosize button").removeClass("active");
		$(event.target).addClass('active');
		
		$(".price").html(this.price);
		$(".rowtotals").html(this.publish.cart.length*this.price);
		$(".shipping").html(this.shipping);
		$(".totals").html(this.publish.cart.length*this.price + this.shipping);
		$(".photocount").html(this.publish.cart.length);
		
		this.publish.checkoutstep = 2;
	  }

	  Infinity.prototype.addToCart = function(image, event){	    
		if(this.publish.cart == null) {
			this.publish.cart = [];
		}
		
		var obj = null; 
		
		if(image != null) {
			obj = JSON.parse(image);
		} else {
			if(this.publish.currentFile == null)
				return;
			else
				obj = this.publish.currentFile;
		}
		
		var imageInCart = false; 
		var cartIndex = 0; 
		
		for (var index = 0; index < this.publish.cart.length; ++index) {
		    if(this.publish.cart[index].id == obj.id) {
			    imageInCart = true; 
			    cartIndex = index; 
		    }
		}
		
		if(!imageInCart) {
			$("#photo-"+obj.id+" .print").addClass("visible");
			this.publish.cart.push(obj);
		} else {
			this.publish.cart.splice(cartIndex, 1);
			$("#photo-"+obj.id+" .print").removeClass("visible");	
		}
		
		this.publish.checkoutstep = 0;
		
		if(this.publish.cart.length > 0) {
			$("#cart").html("("+this.publish.cart.length+")");
		} else  {
			$("#cart").html("");
			this.publish.checkoutstep = -1; 
		}
		
		$('#filesDetailModal').modal('hide');
	  }

	  // Todo, move this from infinity to device 	  
	  Infinity.prototype.showPicture = function(file) {
	  	var obj = JSON.parse(file);
	  	this.publish.currentFile = obj; 
		var imageInCart = false; 
		var cartIndex = 0; 
		
		if(this.publish.cart) {
			for (var index = 0; index < this.publish.cart.length; ++index) {
			    if(this.publish.cart[index].id == obj.id) {
				    imageInCart = true; 
				    cartIndex = index; 
			    }
			}
		}
	  	
		$.ajax({
		    url : "/files/details?id="+obj.id,
			async: false,
			context: this,
		    success : function(result){
				var ts = new Date(null);
				ts.setTime(result.created_at*1000);
				
				var time = new Date(result.created_at*1000);
				var viewMonth = time.getMonth();
				var viewYear = time.getFullYear().toString();
				var viewDate = time.getDate();
				var month = Array("January","February","March","April","May","June","July","August","September","October","November","December");
				
				$("#filesDetailModalLabel").html(result.name+" – "+viewDate +" "+ month[viewMonth] + ", "+viewYear+" – "+result.product_name);
				$("#filesDetailModalLabel").attr("file", obj.id);
				
				if(result.type == "video") {
					$("#moddalVideoContainer").html('<video id="modalVideo" style="display: none;" width="100%" height="520" controls="controls" autoplay="autoplay"><source id="modalSource" src="" type="video/mp4" /></video>');
					
					if(isLocal) {
						$("#modalVideo > source").attr("src", result.abspath.replace("/backupbox/data/devices/", "/static/devices/")+"/"+result.name);
					} else {
						$("#modalVideo > source").attr("src", result.abspath.replace("/backupbox/data/devices/", "/backups/" + username + "/devices/")+"/"+result.name);
					}
				
					$("#modalVideo").load();
					$("#modalVideo").show();
					$("#modalImage").hide();
				} else {
					$("#modalVideo").hide();
					$("#modalImage").show();
					$("#zoomLink").attr("href", "/files/stream/"+result._id+"/null/nodownload/0");
					$("#modalImage").attr("src", "/files/stream/"+result._id+"/null/thumbnail/520");
				}
				
				if(imageInCart) {
					$("#print-label").html("Remove from print queue");
				} else {
					$("#print-label").html("Order Photocopy");
				}
		
		        $('#filesDetailModal').modal('show');				
		    }
		});	  	
  	
	  	//var f = new FileService();
	  	//f.loadDetails(file);	  	
	  }
	  
	  /**
	  * Method that loads next page in the infinite scroll. Device ID and File type ID can be passed as filtering parameters. 
	  *	  
	  **/
	  Infinity.prototype.nextPage = function(_device, _type, noInvert) {
	    // Make sure previous request is not running
	    if (this.busy) return;
	    
	    // Flag this method as running
	    this.busy = true;	
	   	var filters = [];

	    if(_type == "other") {
		    if(!noInvert) {
		    	$("#filter-"+_type).prop("checked", !$("#filter-"+_type).prop("checked"));
		    }

			$("#filter-image").prop("checked", !$("#filter-other").prop("checked"));
			$("#filter-video").prop("checked", !$("#filter-other").prop("checked"));
			
			if(!$("#filter-"+_type).prop("checked")) {
				_type = "image,video";
				this.type = _type;
			}

			filters.push(_type);
	    } else 
	    if(_type != null) {
			this.type = _type;	    	
		    
		    if(!noInvert) {
		    	$("#filter-"+_type).prop("checked", !$("#filter-"+_type).prop("checked"));
		    }
	    	
	    	if($('#filter-other').prop('checked')) {
	    		$('#filter-other').prop('checked', false);
	    	}

			$( "li.filters input" ).each(function( index ) {
			  if($( this ).prop("checked")) {
			  	filters.push($( this ).prop("id").replace("filter-", ""));
			  }
			});
	    }

	    // Parameter to determine wether content was replaced or appended. replace => chnageState = true
	    var changedState = false; 

		// If a device ID was passed, let's filter on device
		if((_device) || _type) {
			changedState = true;
			this.lastCount = -1; 

			if(_device && _device != -1 && this.device != _device) {
				$(".device").removeClass("active");
				$("#"+_device).addClass("active");
				this.device = _device; 
			} else 
			if(_device) {
				this.device = -1; 
				$(".device").removeClass("active");
				$("#allDevices").addClass("active");
				changedState = true; 
				//$(".dropdown-menu").hide();
			}
		}
		
		// Clear visiable area of old images if the state was changed
		if(changedState == true) {
			this.page = 1; 			
			this.publish.items = [];
			this.publish.files = [];
			resetDate();
		}
		
		// Format input string to request page
		if(this.device == null) {
			this.device = -1;
		}

		// Lead request
		if(changedState || this.type != "other" && this.lastCount != 0) {
		$.ajax({
		    url : "/files?after="+this.page+"&device="+this.device+"&format="+filters.join(","),
			async: false,
			context: this,
		    success : function(result){
		    	if(changedState == true) {
					if (!window.matchMedia || (window.matchMedia("(max-width: 767px)").matches)) {
						$("#mainNav").css("height", "0px");
						$("#mainNav").removeClass("in");
						$("#mainNav-btn").addClass("collapsed");
					}
				}

				// If response resulted in no images, show error message
				if(result.files.length == 0 && this.publish.items.length == 0) {
					this.publish.missingImages = true;
				} else {
					this.publish.missingImages = false; 
				}
				
				this.lastCount = result.files.length; 

				// Loop JSON response and add images to ng-repeat array
			    for(var i = 0; i < result.files.length; i++) {
			      var type_content = ""; 
			      
			      // If current item is a video, add info about lenght in thumbnail. 
			      /*if(result.files[i].type == "video" && result.files[i].value != null) {
			      	  var video_length = result.files[i].value.split(" ")
			      	  var suffix = "ms"; 
			      	  
			      	  for (var ind = 0; ind < video_length.length; ++ind) {
			      	  	if(video_length[ind].indexOf(suffix, video_length[ind].length - suffix.length) == -1)
							type_content += video_length[ind].replace("mn", "min")+" ";
					  }
			      }	*/	
			      
			      // Push thumbnail item to ng-repeat array	      
			      if(filters == "other") {
				      var _months = Array("January","February","March","April","May","June","July","August","September","October","November","December");
				      var time = new Date(result.files[i].created_at*1000);
					  var viewMonth = String(_months[time.getMonth()]).substr(0, 3);
					  var viewYear = time.getFullYear().toString();
					  var viewDate = time.getDate();
					  var dat = viewYear + "-" + viewMonth + "-" + viewDate;
					  
				      this.publish.files.push(['<a href="/files/stream/'+result.files[i]._id+'/'+result.files[i].name+'/full/0">'+result.files[i].name+'</a>',result.files[i].type, dat, humanFileSize(result.files[i].size)]);				      
			      } else {
				      this.publish.items.push({background:result.files[i].thumbnail, id:result.files[i].file, created_at:result.files[i].created_at, type:result.files[i].type, type_content:type_content});				      
			      }
			    }			    

				// Increase current page number(for next request)
		        this.page = this.page + 1;
		        this.busy = false;

				if(filters == "other" && this.publish.files.length > 0) {
					this.publish.datatable.fnClearTable();
					this.publish.datatable.fnAddData(this.publish.files);
				}

				if(_type != null) {
					this.type = _type;
				}
			
		    }
		});
		} else {
			this.busy = false; 
		}
	  };
	
	  return Infinity;
	});	

    /**
     * Configure the box app
     */
    box.config(function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise('/');
		
		// When the application starts we are lading device list and first page of the result. 
        $stateProvider
            .state('files', {
                url: '/',
                controller: 'FilesCtrl',
                templateUrl: '/templates/files.html'
            })
    });

    /**
     * Run the box app
     */
    box.run(function ($window) {
        ng.element($window).bind('scroll', function () {
        	// If the appliaction is running on a desktop computer, add fancy paralax scroll to images
            if (false && window.matchMedia && (window.matchMedia("(min-width: 1025px)").matches)) {
	            var winHeight = $($window).height();
	            $('.preview.image').each(function () {
	                var rect = this.getBoundingClientRect(),
	                    el = $(this),
	                    pos,
	                    percent;
	                if (rect.bottom >= 0 && rect.top <= winHeight) {
	                    pos = rect.top / (winHeight - el.height());
	                    percent = Math.round(Math.min(100, Math.max(0,
	                                pos * 100)));
	                    el.css('backgroundPosition', '50% ' + percent + '%');
	                }
	            });
			}
        });
    });

    /**
     * File service
     */
    box.factory('FileService', function ($resource, $window, $q) {

        /**
         *
         */
        var FileService = function () {
            this.filesResource = $resource('/files');
            this.detailsResource = $resource('/files/details');
            this.deviceResource = $resource('/devices');
            this.calendarResource = $resource('/files/calendar');
            this.calendar = [];
            this.devices = [];
            this.missingDevices = false; 
            this.files = [];
            this.details = [];
        };
        FileService.prototype = {

            /**
             * Successful files load callback
             */
            loadFilesSuccess: function (resource) {
                this.files = resource.files;
                //console.log(resource.sql);
            },

            /**
             * Successful calendar load callback
             */
            loadCalendarSuccess: function (data) {
                this.calendar = data;
            },

            /**
             * Successful devices load callback
             */
            loadDevicesSuccess: function (data) {
                this.devices = data.devices;
				$(".navbar").show();
				$("#deviceCount").html("("+this.devices.length+")");
				$(".device-dropdown").click(function() {
					$(".dropdown-menu").toggle();
				});				
            },


            /**
             * Successful file detail load callback
             */
            loadDetailsSuccess: function (data) {
                if (data['_id'] !== undefined) {
                    this.details[data['_id']] = data;
                }
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                //console.log(data);
            },

            /**
             * Load files passing 'filter'
             */
            loadFiles: function (filter, complete) {
                var that = this,
                    args = {}, // arguments
                    fk;        // filter key

                if ($window.devicePixelRatio && $window.devicePixelRatio > 1) {
                    args.retina = 1;
                }

                if (typeof filter === 'object') {
                    for (fk in filter) {
                        if (filter.hasOwnProperty(fk) && filter[fk].length) {
                            args[fk] = filter[fk].join(',');
                        }
                    }
                }

                this.filesResource.get(
                    args,
                    function (data) {
                        that.loadFilesSuccess(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    },
                    function (data) {
                        that.loadError(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    }
                );
                return this;
            },


            /**
             * Load available calendar
             */
            loadCalendar: function () {
                this.calendarResource.get(
                    {},
                    this.loadCalendarSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load available devices
             */
            loadDevices: function () {
                this.deviceResource.get(
                    {},
                    this.loadDevicesSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },
            
            /**
             * Load available filters
             */
            loadFilters: function () {
                this.filterResource.get(
                    {},
                    this.loadFiltersSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load file by id
             */
            loadDetails: function (id) {
                var that = this,
                    deferred = $q.defer(),
                    resource;

                if (this.details[id] !== undefined) {
                    deferred.resolve();
                } else {
                    resource = this.detailsResource.get(
                        {id: id},
                        function (data) {
                            that.loadDetailsSuccess(data);
                            deferred.resolve();
                        },
                        function (data) {
                            that.loadError(data);
                            deferred.resolve();
                        }
                    );
                }

                return deferred.promise;
            },

            /**
             * Get laoded details
             */
            getDetails: function (id) {
                return this.details[id] || false;
            }
        };

        return new FileService();
    });

    /**
     * Files controller
     */
    box.controller('FilesCtrl', function ($scope, $location, FileService, Infinity) {
        this.fileService = FileService.loadFiles().loadDevices();
        $scope.infinity = new Infinity($scope);
        $scope.items = [];
        $scope.files = [];
        $scope.state = "list"; 
        
        if(!$scope.datatable)
	        $scope.datatable = $('#otherfiles').dataTable({ "iDisplayLength": 30, "bLengthChange": false });

        $scope.render = function(e) {
			return $(e).html();
        }

        $scope.FilesCtrl = this;
        return this;
    });

}(window, angular, jQuery || {log: function () { 'use strict'; return; }}));